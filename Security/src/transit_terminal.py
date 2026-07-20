import os
import json
import time
import serial
import tkinter as tk
from tkinter import ttk, messagebox
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager
from graph_engine import GraphEngine

class TransitTerminalApp:
    def __init__(self, root, blueprint_path, policy_path, com_port="COM3"):
        self.root = root
        self.root.title("SMR Core Facility Transit & Access Verification Terminal")
        self.root.geometry("1200x820")
        self.blueprint_path = blueprint_path
        self.policy_path = policy_path

        # Ingest validation engines from active workspace configurations
        self.loader = BlueprintLoader(self.blueprint_path)
        self.rooms = sorted(self.loader.get_all_rooms())

        if not os.path.exists(self.policy_path):
            messagebox.showerror("Initialization Error", "No deployed policy_config.json discovered!\nDeploy a design via the dashboard first.")
            self.root.destroy()
            return

        self.pm = PolicyManager(self.policy_path, self.loader)
        self.engine = GraphEngine(self.loader, self.pm)
        self.zones = ["Zone_1", "Zone_2", "Zone_3", "Zone_4", "Zone_5"]
        self.zone_colors = {
            "Zone_1": "#D4EDDA", "Zone_2": "#FFF3CD", "Zone_3": "#CCE5FF",
            "Zone_4": "#E2D9F3", "Zone_5": "#F8D7DA"
        }

        # Synchronized coordinate matrix matching the dashboard grid
        self.room_coordinates = {
            "protected_area_courtyard":  (130, 30, 780, 380),
            "rad_waste_building":         (150, 60, 260, 120),
            "auxiliary_generator_bldg":   (650, 60, 760, 130),
            "nuclear_receiving":         (300, 50, 430, 110),
            "logistics_change_room":     (300, 110, 430, 150),
            "office_sas_hub":            (470, 290, 610, 360),
            "fuel_service_corridor":     (280, 150, 720, 290),
            "main_control_room":         (310, 190, 460, 250),
            "reactor_containment":       (520, 190, 690, 250),
            "security_gatehouse":        (380, 355, 470, 405),
            "outer_parking":             (220, 430, 360, 490),
            "visitor_center":            (400, 430, 530, 490),
            "maintenance_bypass_tunnel": (60, 150, 110, 460)
        }

        self.portal_coordinates = [
            (370, 455, 390, 465), (415, 400, 435, 410), (415, 350, 435, 360),
            (195, 115, 215, 125), (695, 125, 715, 135), (350, 105, 380, 115),
            (350, 145, 380, 155), (530, 285, 560, 295), (370, 185, 400, 195),
            (590, 185, 620, 195), (105, 450, 115, 470), (195, 175, 205, 185)
        ]

        self.rendering_order = [
            "main_control_room", "reactor_containment", "fuel_service_corridor",
            "nuclear_receiving", "logistics_change_room", "office_sas_hub",
            "rad_waste_building", "auxiliary_generator_bldg", "maintenance_bypass_tunnel",
            "security_gatehouse", "outer_parking", "visitor_center", "protected_area_courtyard"
        ]

        # NTAG215 Hardware Registry Mapping
        self.NFC_REGISTRY = {
            "04:3C:4E:47:9E:61:80": "reactor_operator",
            "04:A1:7C:E2:8F:40:81": "maintenance_technician",
            "04:D2:9A:F2:3C:11:82": "security_officer"
        }

        # Initialize Hardware Serial Connection
        self.ser = None
        self._connect_serial(com_port=com_port)

        self._build_ui()

        # Start non-blocking serial polling loop
        self.root.after(100, self._poll_hardware_serial)

    def _connect_serial(self, com_port="COM3", baud_rate=115200):
        """Attempts to open a connection to the Arduino serial port."""
        try:
            self.ser = serial.Serial(com_port, baud_rate, timeout=0.1)
            time.sleep(1.5)  # Allow Arduino boot time
            print(f"[+] Physical Hardware Terminal Bridge Connected on {com_port}")
        except Exception as e:
            print(f"[!] Hardware Bridge Offline (Running in manual mock mode): {e}")
            self.ser = None

    def _poll_hardware_serial(self):
        """Non-blocking background loop checking for physical NFC taps."""
        if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
            try:
                raw_data = self.ser.readline().decode('utf-8').strip()
                # Verify valid 7-byte UID packet format
                if raw_data and len(raw_data.split(":")) == 7:
                    role = self.NFC_REGISTRY.get(raw_data)
                    if role:
                        self.cb_mock_role.set(role)
                        self.process_simulated_transit(raw_uid=raw_data)
                    else:
                        self.txt_log.delete("1.0", tk.END)
                        self.txt_log.insert(tk.END, f"[X] UNKNOWN TAG DETECTED: {raw_data}\nAccess Denied.")
                        self._flash_access_feedback_glow(is_granted=False)
                        self.ser.write(b'0')
            except Exception as e:
                print(f"[!] Serial Read Error: {e}")

        # Schedule next poll in 50ms
        self.root.after(50, self._poll_hardware_serial)

    def _build_ui(self):
        main_pane = ttk.Frame(self.root, padding="10")
        main_pane.pack(fill=tk.BOTH, expand=True)

        # Left Panel: Live SCADA Floor Plan Status Display
        left_frame = ttk.LabelFrame(main_pane, text=f" Live Plant Access Monitoring Map (Active Config: {self.pm.author_name}) ", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.map_canvas = tk.Canvas(left_frame, bg="#F8F9FA", borderwidth=1, relief="solid")
        self.map_canvas.pack(fill=tk.BOTH, expand=True)

        # Right Panel: Deployment Mission Controls Configuration
        right_frame = ttk.Frame(main_pane, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)

        # Subpanel 1: Spatial Path Trajectory Parameters
        path_group = ttk.LabelFrame(right_frame, text=" 1. Select Target Trajectory Path ", padding="10")
        path_group.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(path_group, text="Origin Starting Room:").pack(anchor="w")
        self.cb_origin = ttk.Combobox(path_group, values=self.rooms, state="readonly")
        self.cb_origin.set("visitor_center")
        self.cb_origin.pack(fill=tk.X, pady=(2, 8))

        ttk.Label(path_group, text="Target Destination Room:").pack(anchor="w")
        self.cb_dest = ttk.Combobox(path_group, values=self.rooms, state="readonly")
        self.cb_dest.set("main_control_room")
        self.cb_dest.pack(fill=tk.X, pady=(2, 5))

        # Subpanel 2: Operational Shift Variables Context
        ctx_group = ttk.LabelFrame(right_frame, text=" 2. Set System Context ", padding="10")
        ctx_group.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(ctx_group, text="Simulated Plant State:").pack(anchor="w")
        self.cb_state = ttk.Combobox(ctx_group, values=["Normal", "Emergency"], state="readonly")
        self.cb_state.set("Normal")
        self.cb_state.pack(fill=tk.X, pady=(2, 8))

        ttk.Label(ctx_group, text="Shift Time hour (0-23):").pack(anchor="w")
        self.spin_hour = ttk.Spinbox(ctx_group, from_=0, to=23, width=10, state="readonly")
        self.spin_hour.set("12")
        self.spin_hour.pack(anchor="w", pady=2)

        # Subpanel 3: Hardware Emulator Trigger (Mock Scanner)
        hw_group = ttk.LabelFrame(right_frame, text=" 3. Hardware Badge Simulator (NTAG215 Emulator) ", padding="10")
        hw_group.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hw_group, text="Select Role Token to Tap:").pack(anchor="w")
        available_roles = list(self.loader.operational_requirements.keys()) + ["contractor"]
        self.cb_mock_role = ttk.Combobox(hw_group, values=available_roles, state="readonly")
        self.cb_mock_role.set("reactor_operator")
        self.cb_mock_role.pack(fill=tk.X, pady=(2, 10))

        btn_tap = ttk.Button(hw_group, text="  Execute Physical Badge Scan Tap", command=self.process_simulated_transit, padding=5)
        btn_tap.pack(fill=tk.X)

        # Subpanel 4: Diagnostic Real-time Output Log Terminal Console
        log_group = ttk.LabelFrame(right_frame, text=" Terminal Console Audit Log ", padding="5")
        log_group.pack(fill=tk.BOTH, expand=True)

        self.txt_log = tk.Text(log_group, bg="#212529", fg="#00FF00", font=("Consolas", 9), wrap=tk.WORD)
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        self._render_base_scada_layout()

    def _render_base_scada_layout(self):
        """Draws the baseline physical environment colorized by active zone allocations."""
        self.map_canvas.delete("all")

        cy_room = "protected_area_courtyard"
        cy_coords = self.room_coordinates[cy_room]
        cy_zone = self.pm.room_to_zone.get(cy_room, "Zone_1")
        self.map_canvas.create_rectangle(
            cy_coords[0], cy_coords[1], cy_coords[2], cy_coords[3],
            fill=self.zone_colors[cy_zone], outline="#6C757D", width=2, dash=(5, 5)
        )
        self.map_canvas.create_text(cy_coords[0] + 130, cy_coords[3] - 20, text=f"courtyard ({cy_zone})", font=("Helvetica", 9, "bold"), fill="#495057")

        for room in reversed(self.rendering_order):
            if room == "protected_area_courtyard": continue
            coords = self.room_coordinates[room]
            zone = self.pm.room_to_zone.get(room, "Zone_1")
            color = self.zone_colors[zone]
            is_vital = room in ["main_control_room", "reactor_containment", "auxiliary_generator_bldg"]
            border_w = 3 if is_vital else 1
            border_c = "#343A40" if is_vital else "#6C757D"
            dash_style = (4, 4) if room == "maintenance_bypass_tunnel" else None
            self.map_canvas.create_rectangle(
                coords[0], coords[1], coords[2], coords[3],
                fill=color, outline=border_c, width=border_w, dash=dash_style, tags=f"room_{room}"
            )

            display_label = room.replace("_", " ")
            if "corridor" in display_label: display_label = "fuel_service\ncorridor"
            elif "tunnel" in display_label: display_label = "maintenance_bypass\ntunnel"
            elif "generator" in display_label: display_label = "auxiliary_gen\nbldg"
            mid_x = (coords[0] + coords[2]) / 2
            mid_y = (coords[1] + coords[3]) / 2
            if room == "fuel_service_corridor":
                self.map_canvas.create_text(coords[0] + 80, coords[1] + 18, text=f"{display_label} ({zone})", font=("Helvetica", 9, "bold"), fill="#212529")
            else:
                self.map_canvas.create_text(mid_x, mid_y, text=f"{display_label}\n({zone})", font=("Helvetica", 8, "bold" if is_vital else "normal"), fill="#212529", justify=tk.CENTER)

        self.map_canvas.create_line(110, 460, 220, 460, fill="#495057", width=2, dash=(2, 2))
        self.map_canvas.create_line(110, 180, 200, 180, fill="#495057", width=2, dash=(2, 2))

        for p_coords in self.portal_coordinates:
            self.map_canvas.create_rectangle(p_coords[0], p_coords[1], p_coords[2], p_coords[3], fill="#212529", outline="#FFFFFF", width=1)

    def process_simulated_transit(self, raw_uid=None):
        """Intercepts variables, invokes graph verification, outputs maps, and sends hardware signals."""
        self.map_canvas.delete("vector_line")
        self.txt_log.delete("1.0", tk.END)

        origin = self.cb_origin.get()
        destination = self.cb_dest.get()
        role = self.cb_mock_role.get()
        state = self.cb_state.get()
        hour = int(self.spin_hour.get())

        context_dict = {
            "system_state": state,
            "time_of_day": hour,
            "active_escorts": ["security_officer"] if role == "maintenance_technician" else [],
            "present_roles": [role, "security_officer"] if role == "maintenance_technician" else [role],
            "guards_distracted": False
        }

        if raw_uid:
            self.txt_log.insert(tk.END, f"[+] PHYSICAL HARDWARE TAP DETECTED (UID: {raw_uid})\n")
        else:
            self.txt_log.insert(tk.END, f"[*] MANUAL SIMULATION INIT: Emulating tap for '{role}'...\n")

        self.txt_log.insert(tk.END, f"[*] Path: {origin} -> {destination}\n")
        self.txt_log.insert(tk.END, f"[*] State: {state} | Time: {hour}:00\n")
        self.txt_log.insert(tk.END, "-" * 40 + "\n")

        report = self.engine.verify_path(origin, destination, role, context_dict)

        # Filter out repetitive debug checks to keep console clean and readable
        for entry in report["audit_trail"]:
            if "Sequence Verified" in entry:
                continue
            self.txt_log.insert(tk.END, f" {entry}\n")

        if report["path_found"]:
            self.txt_log.insert(tk.END, "\n[✔] ACCESS AUTHORIZED (TERMINAL UNLOCKED)\n")
            self.txt_log.insert(tk.END, f"Total Delay: {report['total_time']} minutes.")
            self._draw_routing_vector_trajectory(report["path"])
            self._flash_access_feedback_glow(is_granted=True)

            if self.ser and self.ser.is_open:
                self.ser.write(b'1')
        else:
            self.txt_log.insert(tk.END, "\n[X] DENIED: BOUNDARY TRANSIT REJECTED\n")
            self._flash_access_feedback_glow(is_granted=False)

            if self.ser and self.ser.is_open:
                self.ser.write(b'0')

        self.txt_log.see(tk.END)

    def _get_room_waypoint(self, room):
        """Returns the visual coordinate for path vector lines, handling large area overlays."""
        if room == "protected_area_courtyard":
            # Override courtyard midpoint to open space just above the security gatehouse
            return (425, 330)
        coords = self.room_coordinates[room]
        return ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)

    def _draw_routing_vector_trajectory(self, path_nodes):
        """Traces a navigational vector connecting room midpoints."""
        points = [self._get_room_waypoint(room) for room in path_nodes]

        for i in range(len(points) - 1):
            self.map_canvas.create_line(
                points[i][0], points[i][1], points[i+1][0], points[i+1][1],
                fill="#0056B3", width=4, arrow=tk.LAST, tags="vector_line"
            )
            self.map_canvas.create_oval(
                points[i][0]-4, points[i][1]-4, points[i][0]+4, points[i][1]+4,
                fill="#00FFF0", outline="#0056B3", width=1, tags="vector_line"
            )

    def _flash_access_feedback_glow(self, is_granted=True):
        """Flashes outer window border to replicate hardware feedback LEDs."""
        flash_color = "#28A745" if is_granted else "#DC3545"
        alert_box = self.map_canvas.create_rectangle(
            5, 5, 800, 550, outline=flash_color, width=6
        )
        self.root.after(400, lambda: self.map_canvas.delete(alert_box))

if __name__ == "__main__":
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(src_dir)
    b_path = os.path.join(root_dir, "data", "facility_blueprint.json")
    p_path = os.path.join(root_dir, "data", "policy_config.json")

    root_window = tk.Tk()
    app = TransitTerminalApp(root_window, b_path, p_path, com_port="COM3")
    root_window.mainloop()