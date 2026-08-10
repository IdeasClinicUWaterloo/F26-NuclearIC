import unittest

import numpy as np

from controller.control import Controller
from controller.state_machine import SafetySupervisor
from reactor.model import ReactorModel
from reactor.sensors import Sensor, SensorSuite
from run.simulation import Simulation


class ControllerTests(unittest.TestCase):
    def test_derivative_starts_without_a_kick(self):
        controller = Controller(kp=0.0, ki=0.0, kd=1.0, max_speed=10.0)

        self.assertEqual(controller.update(1.0, 0.0, 0.1), 0.0)
        self.assertEqual(controller.update(1.0, 0.5, 0.1), -5.0)

    def test_integral_stops_at_saturation(self):
        controller = Controller(kp=0.0, ki=1.0, kd=0.0, max_speed=0.1)

        self.assertEqual(controller.update(1.0, 0.0, 1.0), 0.1)
        self.assertEqual(controller.integral, 0.0)

    def test_rejects_invalid_timestep(self):
        controller = Controller(kp=1.0, ki=0.0, kd=0.0)

        with self.assertRaises(ValueError):
            controller.update(1.0, 1.0, 0.0)


class SafetySupervisorTests(unittest.TestCase):
    def setUp(self):
        self.supervisor = SafetySupervisor(
            limits={
                "power": {"warn": 1.05, "limit": 1.10, "scram": 1.25}
            },
            rho_min=-5e-4,
            rho_max=5e-4,
        )

    def test_unavailable_reading_raises_warning(self):
        state = self.supervisor.evaluate({"power": np.nan})

        self.assertEqual(state, "WARNING")
        self.assertEqual(
            self.supervisor.triggers, ["power reading is unavailable"]
        )

    def test_scram_latches_until_shutdown(self):
        self.assertEqual(self.supervisor.evaluate({"power": 1.25}), "SCRAM")
        self.assertEqual(self.supervisor.apply(5e-4), -0.02)

        self.assertEqual(self.supervisor.evaluate({"power": 1.0}), "SCRAM")
        self.assertEqual(self.supervisor.evaluate({"power": 0.01}), "SHUTDOWN")
        self.assertEqual(self.supervisor.evaluate({"power": 1.0}), "SHUTDOWN")


class SensorTests(unittest.TestCase):
    def test_seed_reproduces_sensor_noise(self):
        state = ReactorModel().x0
        first = SensorSuite(seed=7).read_all(state, rho_rod=0.0)
        second = SensorSuite(seed=7).read_all(state, rho_rod=0.0)

        self.assertEqual(first, second)

    def test_stuck_sensor_keeps_its_first_sample(self):
        sensor = Sensor(sigma=0.0)
        sensor.set_fault("stuck")

        self.assertEqual(sensor.read(10.0), 10.0)
        self.assertEqual(sensor.read(20.0), 10.0)

    def test_rejects_unknown_fault(self):
        with self.assertRaises(ValueError):
            Sensor(sigma=0.1).set_fault("noisy")


class ReactorModelTests(unittest.TestCase):
    def test_initial_state_is_steady_without_a_disturbance(self):
        model = ReactorModel(disturbance_magnitude=0.0)

        np.testing.assert_allclose(
            model.dynamics(0.0, model.x0),
            np.zeros_like(model.x0),
            atol=1e-10,
        )


class SimulationTests(unittest.TestCase):
    def test_histories_align_with_partial_final_step(self):
        simulator = Simulation(duration=0.25, dt=0.1)
        final_state = simulator.simulate(
            Controller(kp=3e-4, ki=0.0, kd=0.0),
            SensorSuite(seed=3),
        )

        self.assertEqual(final_state.shape, (10,))
        self.assertEqual(len(simulator.time_steps), 4)
        self.assertEqual(len(simulator.control_times), 3)
        self.assertAlmostEqual(simulator.time_steps[-1], 0.25)
        self.assertAlmostEqual(sum(simulator.control_durations), 0.25)

    def test_control_rod_fault_does_not_block_scram(self):
        simulator = Simulation(duration=0.1, dt=0.1)
        supervisor = SafetySupervisor(
            limits={
                "power": {"warn": -3.0, "limit": -2.0, "scram": -1.0},
                "fuel_temp": {"warn": 1e3, "limit": 2e3, "scram": 3e3},
                "coolant_temp": {"warn": 1e3, "limit": 2e3, "scram": 3e3},
            },
            rho_min=-5e-4,
            rho_max=5e-4,
        )
        simulator._build_safety_supervisor = lambda: supervisor

        simulator.simulate(
            Controller(kp=3e-4, ki=0.0, kd=0.0),
            SensorSuite(seed=4),
            actuator_fault={"type": "stuck", "t_start": 0.0},
        )

        self.assertEqual(simulator.safety_states, ["SCRAM"])
        self.assertEqual(simulator.control_values, [-0.02])


if __name__ == "__main__":
    unittest.main()
