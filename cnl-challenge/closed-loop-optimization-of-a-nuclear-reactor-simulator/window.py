from pathlib import Path
import json
import time
from playwright.sync_api import sync_playwright

URL = "https://dalton-nrs.manchester.ac.uk/"
LOG_PATH = Path("bot_log.jsonl")

POLL_SEC = 0.5

def clamp(x, lo, hi):
    return max(lo, min(hi, x))

def append_log(obj):
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(obj) + "\n")

READ_STATE_JS = """
() => {
    const sim = window.game.simulation;
    const ui = window.ui.instruments;

    return {
        sim: {
            ControlRodPosition: sim.ControlRodPosition,
            CoolantFlowRate: sim.CoolantFlowRate,
            SteamFlowRate: sim.SteamFlowRate,
            ReactorCoreTemperature: sim.ReactorCoreTemperature,
            CoolantTemperature: sim.CoolantTemperature,
            GeneratorOutput: sim.GeneratorOutput,
            GeneratorOutputMW: sim.GeneratorOutputMW,
            PowerDemand: sim.PowerDemand,
            PowerTolerance: sim.PowerTolerance,
            TimeOfDay: sim.TimeOfDay,
            EndOfDay: sim.EndOfDay,
            GameStarted: !!sim.HasPlayerStarted
        },
        ui: {
            reactor: ui.reactor.value,
            coolant: ui.coolant.value,
            steam: ui.steam.value
        },
        game: {
            score: window.game.score,
            currentScore: window.game.currentScore,
            gameOver: window.game.Gameover,
            paused: window.game.Paused
        }
    };
}
"""

WRITE_CONTROLS_JS = """
({rod, steam, coolant}) => {
    const ui = window.ui.instruments;
    ui.coolant.setSliderValue(coolant);
    ui.reactor.setSliderValue(rod);
    ui.steam.setSliderValue(steam);
    return {
        reactor: ui.reactor.value,
        coolant: ui.coolant.value,
        steam: ui.steam.value
    };
}
"""

def decide_controls(state, prev):
    sim = state["sim"]

    demand = sim["PowerDemand"]
    output = sim["GeneratorOutputMW"]
    error = demand - output

    rod_now = state["ui"]["reactor"]
    steam_now = state["ui"]["steam"]
    core_temp = sim["ReactorCoreTemperature"]
    coolant_temp = sim["CoolantTemperature"]
    tol = sim["PowerTolerance"]

    coolant_target = 100
    rod_target = rod_now
    steam_target = steam_now

    mode = prev.get("mode", "startup")

    # hard safety first
    if core_temp > 99:
        mode = "recovery"
        rod_target -= 6
        steam_target -= 8
        return clamp(rod_target, 0, 100), clamp(steam_target, 0, 100), coolant_target, {
            "mode": mode,
            "error": error
        }

    # hysteresis on coolant recovery
    if mode != "recovery" and coolant_temp < 289.2:
        mode = "recovery"

    if mode == "recovery":
        rod_target -= 4
        steam_target -= 6

        # once coolant has clearly recovered, restart gently
        if coolant_temp > 290.2:
            mode = "startup"
            rod_target = min(rod_target, 8)
            steam_target = min(steam_target, 2)

        return clamp(rod_target, 0, 100), clamp(steam_target, 0, 100), coolant_target, {
            "mode": mode,
            "error": error
        }

    # startup phase
    if mode == "startup":
        if coolant_temp < 290.0:
            rod_target = 0
            steam_target = 0
            return rod_target, steam_target, coolant_target, {
                "mode": mode,
                "error": error
            }

        # gentle staged ramp
        if rod_now < 6:
            rod_target = 6
            steam_target = 0
        elif rod_now < 10:
            rod_target = 10
            steam_target = min(steam_now, 2)
        elif output < 200:
            rod_target = min(12, rod_now + 1)
            steam_target = min(5, steam_now + 2)
        else:
            mode = "tracking"

        return clamp(rod_target, 60, 100), clamp(steam_target, 60, 100), coolant_target, {
            "mode": mode,
            "error": error
        }

    # tracking mode
    if demand >= 1500:
        rod_floor = 72
    elif demand >= 1400:
        rod_floor = 67
    elif demand >= 1300:
        rod_floor = 62
    elif demand >= 1200:
        rod_floor = 58
    elif demand >= 1100:
        rod_floor = 54
    else:
        rod_floor = 48

    rod_target = max(rod_target, rod_floor)

    if demand >= 1500:
        steam_floor = 72
    elif demand >= 1400:
        steam_floor = 68
    elif demand >= 1300:
        steam_floor = 64
    elif demand >= 1200:
        steam_floor = 60
    elif demand >= 1100:
        steam_floor = 56
    else:
        steam_floor = 52

    steam_target = max(steam_target, steam_floor)

    if error > 250:
        steam_target += 5
        rod_target += 2
    elif error > 100:
        steam_target += 3
        rod_target += 1
    elif error > 50:
        steam_target += 1
        rod_target += 1
    elif error < -250:
        steam_target -= 4
        rod_target -= 2
    elif error < -100:
        steam_target -= 2
        rod_target -= 1
    elif error < -50:
        steam_target -= 1   
        rod_target -= 1

    if coolant_temp < 289.8:
        steam_target -= 1
        rod_target -= 1
    elif coolant_temp > 290.4 and error > 0:
        rod_target += 1

    if steam_now > 60 and error > 100:
        rod_target += 2

    if core_temp > 72:
        rod_target -= 2
        steam_target -= 2
    elif core_temp < 45 and error > 100:
        rod_target += 1

    steam_target = min(steam_target, rod_target + 30)

    rod_target = clamp(rod_target, prev["rod"] - 3, prev["rod"] + 3)
    steam_target = clamp(steam_target, prev["steam"] - 4, prev["steam"] + 4)

    return clamp(rod_target, 0, 100), clamp(steam_target, 0, 100), coolant_target, {
        "mode": mode,
        "error": error
    }

def main():
    if LOG_PATH.exists():
        LOG_PATH.unlink()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False, slow_mo=20)
        page = browser.new_page()
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(5000)

        print("Start the game manually and get to live gameplay.")
        input("Press ENTER when the level is running...")

        prev = {"rod": 0.0, "steam": 0.0, "mode": "startup"}

        # Force safe initial state
        page.evaluate(WRITE_CONTROLS_JS, {"rod": 0, "steam": 0, "coolant": 100})
        time.sleep(1.0)

        pause_count = 0

        for step in range(1000):
            state = page.evaluate(READ_STATE_JS)

            if state["game"]["paused"]:
                pause_count += 1
            else:
                pause_count = 0

            if pause_count >= 3:
                print("Paused for 3 consecutive polls, stopping.")
                append_log({"step": step, "event": "paused_stop", "state": state})
                break

            if state["game"]["gameOver"]:
                print("Game over detected.")
                append_log({"step": step, "event": "game_over", "state": state})
                break

            rod, steam, coolant, meta = decide_controls(state, prev)

            applied = page.evaluate(WRITE_CONTROLS_JS, {
                "rod": rod,
                "steam": steam,
                "coolant": coolant
            })

            log_row = {
                "step": step,
                "timestamp": time.time(),
                "state": state,
                "command": {
                    "rod": rod,
                    "steam": steam,
                    "coolant": coolant
                },
                "applied_ui": applied,
                "meta": meta
            }
            append_log(log_row)

            print(
                f"step={step:04d} "
                f"demand={state['sim']['PowerDemand']:4.0f} "
                f"out={state['sim']['GeneratorOutputMW']:4.0f} "
                f"err={meta['error']:5.0f} "
                f"core={state['sim']['ReactorCoreTemperature']:5.1f} "
                f"cool={state['sim']['CoolantTemperature']:5.1f} "
                f"rod->{rod:5.1f} "
                f"steam->{steam:5.1f} "
                f"mode={meta['mode']}"
            )

            prev["rod"] = rod
            prev["steam"] = steam
            prev["mode"] = meta["mode"]
            time.sleep(POLL_SEC)

        input("Press ENTER to close...")
        browser.close()

if __name__ == "__main__":
    main()