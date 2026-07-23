import os
import json
import time
import serial
import serial.tools.list_ports
import tkinter as tk
from tkinter import ttk, messagebox
from blueprint_loader import BlueprintLoader
from policy_manager import PolicyManager
from graph_engine import GraphEngine

class UnifiedSMRSecurityTerminal:
    def __init__(self, root, blueprint_path, policy_path):
        self.root = root
        self.root.title("SMR Physical Protection Access Management & Verification Terminal")
        self.root.geometry("1250x850")
        self.blueprint_path = blueprint_path
        self.policy_path = policy_path

        # 1. Load Blueprint and Baseline Data
        self.loader = BlueprintLoader(self.blueprint_path)
        self.rooms = sorted(self.loader.get_all_rooms())
        self.roles = list(self.loader.operational_requirements.keys())
        self.zones = ["Zone_1", "Zone_2", "Zone_3", "Zone_4", "Zone_5"]
        self.states = ["Normal", "Emergency"]
        self.access_options = ["Permitted", "Restricted", "Denied"]

        self.zone_colors = {
            "Zone_1": "#D4EDDA", "Zone_2": "#FFF3CD", "Zone_3": "#CCE5FF",
            "Zone_4": "#E2D9F3", "Zone_5": "#F8D7DA"
        }

        # Spatial Coordinates Mapping
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
            (370, 455, 390, 465, "visitor_center", "outer_parking"),
            (415, 400, 435, 410, "outer_parking", "security_gatehouse"),
            (415, 350, 435, 360, "security_gatehouse", "protected_area_courtyard"),
            (195, 115, 215, 125, "protected_area_courtyard", "rad_waste_building"),
            (695, 125, 715, 135, "protected_area_courtyard", "auxiliary_generator_bldg"),
            (350, 45, 380, 55, "protected_area_courtyard", "nuclear_receiving"),
            (520, 355, 560, 365, "protected_area_courtyard", "office_sas_hub"),
            (350, 105, 380, 115, "nuclear_receiving", "logistics_change_room"),
            (350, 145, 380, 155, "logistics_change_room", "fuel_service_corridor"),
            (530, 285, 560, 295, "office_sas_hub", "fuel_service_corridor"),
            (370, 185, 400, 195, "fuel_service_corridor", "main_control_room"),
            (590, 185, 620, 195, "fuel_service_corridor", "reactor_containment"),
            (105, 450, 115, 470, "outer_parking", "maintenance_bypass_tunnel"),
            (195, 175, 205, 185, "maintenance_bypass_tunnel", "fuel_service_corridor")
        ]

        self.collision_check_order = [
            "main_control_room", "reactor_containment", "fuel_service_corridor",
            "nuclear_receiving", "logistics_change_room", "office_sas_hub",
            "rad_waste_building", "auxiliary_generator_bldg", "maintenance_bypass_tunnel",
            "security_gatehouse", "outer_parking", "visitor_center", "protected_area_courtyard"
        ]

        # NTAG215 Hardware Map
        self.NFC_REGISTRY = {
            "04:3E:5B:A2:91:5D:80": "reactor_operator",
            "04:A1:7C:E2:8F:40:81": "maintenance_technician",
            "04:D2:9A:F2:3C:11:82": "security_officer",
            "04:49:CA:43:9E:61:80": "reactor_operator"
        }

        # Initialize Design Data State
        self.room_zone_mapping = {}
        self.policy_matrix_data = {}
        self._initialize_default_policy_data()

        # Engine objects (Instantiated upon policy deployment)
        self.pm = None
        self.engine = None
        self._try_load_existing_policy_engine()

        # Initialize Hardware Connection
        self.ser = None
        self._connect_serial()

        # Build GUI
        self._build_ui()

        # Start non-blocking serial listener
        self.root.after(100, self._poll_hardware_serial)

    # ------------------------------------------------------------------
    #  HARDWARE & POLICY ENGINE MANAGEMENT
    # ------------------------------------------------------------------
    def _try_load_existing_policy_engine(self):
        """Attempts to load PolicyManager and GraphEngine if policy_config.json exists."""
        if os.path.exists(self.policy_path):
            try:
                self.pm = PolicyManager(self.policy_path, self.loader)
                self.engine = GraphEngine(self.loader, self.pm)
            except Exception as e:
                print(f"[!] Warning loading existing policy: {e}")

    def _auto_detect_arduino_port(self):
        """Scans system ports for connected microcontrollers."""
        ports = list(serial.tools.list_ports.comports())
        for port in ports:
            desc = port.description.lower()
            device = port.device.lower()
            if any(k in desc or k in device for k in ["arduino", "renesas", "acm", "usbserial", "ch340", "cp210"]):
                print(f"[+] Auto-detected hardware on {port.device}")
                return port.device
        if ports:
            return ports[0].device
        return None

    def _connect_serial(self, com_port=None):
        """Connects to the hardware serial port."""
        target_port = com_port if com_port else self._auto_detect_arduino_port()
        if not target_port:
            print("[!] No active serial ports found. Hardware running in manual mock mode.")
            self.ser = None
            return

        try:
            self.ser = serial.Serial(target_port, 115200, timeout=0.1)
            time.sleep(1.5)
            print(f"[+] Hardware Terminal Bridge Connected on {target_port}")
        except Exception as e:
            print(f"[!] Hardware Bridge Offline: {e}")
            self.ser = None

    def _poll_hardware_serial(self):
        """Background listener loop for hardware NFC taps."""
        if self.ser and self.ser.is_open and self.ser.in_waiting > 0:
            try:
                raw_data = self.ser.readline().decode('utf-8').strip()
                if raw_data and len(raw_data.split(":")) == 7:
                    role = self.NFC_REGISTRY.get(raw_data)
                    if role:
                        self.cb_mock_role.set(role)
                        # Switch to Tab 3 automatically on hardware tap if desired
                        self.notebook.select(self.tab3)
                        self.process_simulated_transit(raw_uid=raw_data)
                    else:
                        self.notebook.select(self.tab3)
                        self.txt_log.delete("1.0", tk.END)
                        self.txt_log.insert(tk.END, f"[X] UNKNOWN TAG DETECTED: {raw_data}\nAccess Denied.")
                        self._flash_access_feedback_glow(is_granted=False)
                        self.ser.write(b'0')
            except Exception as e:
                print(f"[!] Serial Read Error: {e}")

        self.root.after(50, self._poll_hardware_serial)

    def _initialize_default_policy_data(self):
        """Seeds baseline design attributes in memory."""
        for zone in self.zones:
            self.policy_matrix_data[zone] = {}
            for state in self.states:
                st_lower = state.lower()
                self.policy_matrix_data[zone][st_lower] = {}
                for role in self.roles:
                    self.policy_matrix_data[zone][st_lower][role] = {
                        "access": "Permitted",
                        "requires_escort": False,
                        "escort_role": "security_officer",
                        "start_hour": 0,
                        "end_hour": 23,
                        "zone_dependency": "None"
                    }
        for room in self.rooms:
            self.room_zone_mapping[room] = "Zone_1"

    # ------------------------------------------------------------------
    #  GUI CONSTRUCTION & TABS
    # ------------------------------------------------------------------
    def _build_ui(self):
        main_container = ttk.Frame(self.root, padding="10")
        main_container.pack(fill=tk.BOTH, expand=True)

        # Header Frame
        meta_frame = ttk.LabelFrame(main_container, text=" Configuration Metadata ", padding="10")
        meta_frame.pack(fill=tk.X, pady=(0, 10))
        ttk.Label(meta_frame, text="System Engineer / Group Name:").pack(side=tk.LEFT, padx=5)
        self.author_entry = ttk.Entry(meta_frame, width=30)
        self.author_entry.insert(0, "Systems_Engineering_Group_A")
        self.author_entry.pack(side=tk.LEFT, padx=5)

        # Master Notebook (Tabs)
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Build 3 Clean Tabs
        self.tab1 = ttk.Frame(self.notebook, padding="10")
        self.tab2 = ttk.Frame(self.notebook, padding="10")
        self.tab3 = ttk.Frame(self.notebook, padding="10")

        self.notebook.add(self.tab1, text=" 1. Interactive Zone Map Editor ")
        self.notebook.add(self.tab2, text=" 2. Role Permissions Matrix ")
        self.notebook.add(self.tab3, text=" 3. Live Hardware & Transit SCADA Monitor ")

        self._build_spatial_mapping_tab()
        self._build_policy_matrix_tab()
        self._build_transit_terminal_tab()

        # Global Deploy Footer
        deploy_frame = ttk.Frame(main_container)
        deploy_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=2)
        btn_deploy = ttk.Button(
            deploy_frame,
            text="  Compile, Deploy & Hot-Reload Security Policy",
            command=self.export_and_reload_policy,
            padding="8"
        )
        btn_deploy.pack(fill=tk.X)

    # --- TAB 1: SPATIAL MAP EDITOR ---
    def _build_spatial_mapping_tab(self):
        vis_panel = ttk.Frame(self.tab1, padding="5")
        vis_panel.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(vis_panel, text="Audit Clearance Path For:", font=("Helvetica", 9, "bold")).pack(side=tk.LEFT, padx=5)
        self.map_role_filter = ttk.Combobox(vis_panel, values=self.roles, width=22, state="readonly")
        self.map_role_filter.set(self.roles[0])
        self.map_role_filter.pack(side=tk.LEFT, padx=5)
        self.map_role_filter.bind("<<ComboboxSelected>>", lambda e: self._redraw_design_map())

        ttk.Label(vis_panel, text="Simulated State:").pack(side=tk.LEFT, padx=15)
        self.map_state_filter = ttk.Combobox(vis_panel, values=self.states, width=12, state="readonly")
        self.map_state_filter.set("Normal")
        self.map_state_filter.pack(side=tk.LEFT, padx=5)
        self.map_state_filter.bind("<<ComboboxSelected>>", lambda e: self._redraw_design_map())

        map_wrapper = ttk.LabelFrame(self.tab1, text=" Site Layout Plan (Left-Click rooms to assign security zones) ", padding="10")
        map_wrapper.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.editor_canvas = tk.Canvas(map_wrapper, bg="#F8F9FA", borderwidth=1, relief="solid")
        self.editor_canvas.pack(fill=tk.BOTH, expand=True)
        self.editor_canvas.bind("<Button-1>", self._handle_editor_map_click)

        self._redraw_design_map()

    def _redraw_design_map(self):
        self.editor_canvas.delete("all")
        cy_room = "protected_area_courtyard"
        cy_coords = self.room_coordinates[cy_room]
        cy_zone = self.room_zone_mapping[cy_room]
        self.editor_canvas.create_rectangle(
            cy_coords[0], cy_coords[1], cy_coords[2], cy_coords[3],
            fill=self.zone_colors[cy_zone], outline="#6C757D", width=2, dash=(5, 5)
        )
        self.editor_canvas.create_text(cy_coords[0] + 130, cy_coords[3] - 20, text=f"courtyard ({cy_zone})", font=("Helvetica", 9, "bold"), fill="#495057")

        for room in reversed(self.collision_check_order):
            if room == "protected_area_courtyard": continue
            coords = self.room_coordinates[room]
            zone = self.room_zone_mapping[room]
            color = self.zone_colors[zone]
            is_vital = room in ["main_control_room", "reactor_containment", "auxiliary_generator_bldg"]
            border_w = 3 if is_vital else 1
            border_c = "#343A40" if is_vital else "#6C757D"
            dash_style = (4, 4) if room == "maintenance_bypass_tunnel" else None

            self.editor_canvas.create_rectangle(
                coords[0], coords[1], coords[2], coords[3],
                fill=color, outline=border_c, width=border_w, dash=dash_style
            )

            display_label = room.replace("_", " ")
            if "corridor" in display_label: display_label = "fuel_service\ncorridor"
            elif "tunnel" in display_label: display_label = "maintenance_bypass\ntunnel"
            elif "generator" in display_label: display_label = "auxiliary_gen\nbldg"
            mid_x = (coords[0] + coords[2]) / 2
            mid_y = (coords[1] + coords[3]) / 2

            if room == "fuel_service_corridor":
                self.editor_canvas.create_text(coords[0] + 80, coords[1] + 18, text=f"{display_label} ({zone})", font=("Helvetica", 9, "bold"), fill="#212529")
            else:
                self.editor_canvas.create_text(mid_x, mid_y, text=f"{display_label}\n({zone})", font=("Helvetica", 9, "bold" if is_vital else "normal"), fill="#212529", justify=tk.CENTER)

        # Portals SCADA Preview
        active_role = self.map_role_filter.get()
        active_state = self.map_state_filter.get().lower()
        for p_coords in self.portal_coordinates:
            px1, py1, px2, py2, room_a, room_b = p_coords
            zone_a = self.room_zone_mapping[room_a]
            zone_b = self.room_zone_mapping[room_b]
            rules_a = self.policy_matrix_data[zone_a][active_state][active_role]
            rules_b = self.policy_matrix_data[zone_b][active_state][active_role]

            if rules_a["access"] == "Denied" or rules_b["access"] == "Denied":
                portal_color = "#DC3545"
            elif rules_a["requires_escort"] or rules_b["requires_escort"]:
                portal_color = "#FFC107"
            else:
                portal_color = "#28A745"

            self.editor_canvas.create_rectangle(px1, py1, px2, py2, fill=portal_color, outline="#343A40", width=1)

    def _handle_editor_map_click(self, event):
        click_x, click_y = event.x, event.y
        detected_room = None
        for room in self.collision_check_order:
            coords = self.room_coordinates[room]
            if coords[0] <= click_x <= coords[2] and coords[1] <= click_y <= coords[3]:
                detected_room = room
                break
        if detected_room:
            popup = tk.Menu(self.root, tearoff=0)
            for z in self.zones:
                popup.add_command(label=f"Assign to {z}", command=lambda target_z=z, r=detected_room: self._update_room_zone(r, target_z))
            popup.post(event.x_root, event.y_root)

    def _update_room_zone(self, room_name, target_zone):
        self.room_zone_mapping[room_name] = target_zone
        self._redraw_design_map()
        if hasattr(self, 'scada_canvas'):
            self._render_live_scada_layout()

    # --- TAB 2: PERMISSIONS MATRIX ---
    def _build_policy_matrix_tab(self):
        selector_frame = ttk.Frame(self.tab2, padding="5")
        selector_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(selector_frame, text="Select Target Security Ring:").pack(side=tk.LEFT, padx=5)
        self.active_zone_filter = ttk.Combobox(selector_frame, values=self.zones, width=12, state="readonly")
        self.active_zone_filter.set("Zone_1")
        self.active_zone_filter.pack(side=tk.LEFT, padx=5)
        self.active_zone_filter.bind("<<ComboboxSelected>>", lambda e: self._refresh_permission_matrix_display())

        ttk.Label(selector_frame, text="Select Operational Plant State:").pack(side=tk.LEFT, padx=25)
        self.active_state_filter = ttk.Combobox(selector_frame, values=self.states, width=15, state="readonly")
        self.active_state_filter.set("Normal")
        self.active_state_filter.pack(side=tk.LEFT, padx=5)
        self.active_state_filter.bind("<<ComboboxSelected>>", lambda e: self._refresh_permission_matrix_display())

        self.matrix_wrapper = ttk.LabelFrame(self.tab2, text=" Role-Based Clearances Configuration ", padding="10")
        self.matrix_wrapper.pack(fill=tk.BOTH, expand=True)
        self._refresh_permission_matrix_display()

    def _refresh_permission_matrix_display(self):
        for widget in self.matrix_wrapper.winfo_children():
            widget.destroy()

        target_z = self.active_zone_filter.get()
        target_s = self.active_state_filter.get().lower()

        headers_row = ttk.Frame(self.matrix_wrapper)
        headers_row.pack(fill=tk.X, pady=5)
        ttk.Label(headers_row, text="Personnel Role Profile", font='Helvetica 10 bold', width=22, anchor="w").pack(side=tk.LEFT, padx=5)
        ttk.Label(headers_row, text="Access Rule", font='Helvetica 10 bold', width=12, anchor="center").pack(side=tk.LEFT, padx=5)
        ttk.Label(headers_row, text="Hours (Start-End)", font='Helvetica 10 bold', width=16, anchor="center").pack(side=tk.LEFT, padx=5)
        ttk.Label(headers_row, text="Escort Required", font='Helvetica 10 bold', width=15, anchor="center").pack(side=tk.LEFT, padx=5)
        ttk.Label(headers_row, text="Prerequisite Zone Dependency", font='Helvetica 10 bold', width=26, anchor="center").pack(side=tk.LEFT, padx=5)
        ttk.Separator(self.matrix_wrapper, orient="horizontal").pack(fill=tk.X, pady=5)

        for role in self.roles:
            row_frame = ttk.Frame(self.matrix_wrapper, padding="5")
            row_frame.pack(fill=tk.X, pady=4)
            ttk.Label(row_frame, text=role, width=22, font='Helvetica 10', anchor="w").pack(side=tk.LEFT, padx=5)

            current_config = self.policy_matrix_data[target_z][target_s][role]

            acc_var = tk.StringVar(value=current_config["access"])
            cb_acc = ttk.Combobox(row_frame, textvariable=acc_var, values=self.access_options, width=12, state="readonly")
            cb_acc.pack(side=tk.LEFT, padx=5)
            cb_acc.bind("<<ComboboxSelected>>", lambda e, r=role, v=acc_var: self._save_live_grid_value(r, "access", v.get()))

            time_frame = ttk.Frame(row_frame)
            time_frame.pack(side=tk.LEFT, padx=12)
            sh_var = tk.StringVar(value=str(current_config["start_hour"]))
            eh_var = tk.StringVar(value=str(current_config["end_hour"]))
            sp_sh = ttk.Spinbox(time_frame, from_=0, to=23, textvariable=sh_var, width=4, state="readonly")
            sp_sh.pack(side=tk.LEFT)
            sp_sh.bind("<ButtonRelease-1>", lambda e, r=role, v=sh_var: self._save_live_grid_value(r, "start_hour", int(v.get())))
            ttk.Label(time_frame, text="-").pack(side=tk.LEFT, padx=2)
            sp_eh = ttk.Spinbox(time_frame, from_=0, to=23, textvariable=eh_var, width=4, state="readonly")
            sp_eh.pack(side=tk.LEFT)
            sp_eh.bind("<ButtonRelease-1>", lambda e, r=role, v=eh_var: self._save_live_grid_value(r, "end_hour", int(v.get())))

            esc_var = tk.BooleanVar(value=current_config["requires_escort"])
            chk_esc = ttk.Checkbutton(row_frame, variable=esc_var, width=15)
            chk_esc.pack(side=tk.LEFT, padx=20)
            chk_esc.configure(command=lambda r=role, v=esc_var: self._save_live_grid_value(r, "requires_escort", v.get()))

            dep_options = ["None"] + self.zones
            dep_var = tk.StringVar(value=current_config["zone_dependency"])
            cb_dep = ttk.Combobox(row_frame, textvariable=dep_var, values=dep_options, width=22, state="readonly")
            cb_dep.pack(side=tk.LEFT, padx=5)
            cb_dep.bind("<<ComboboxSelected>>", lambda e, r=role, v=dep_var: self._save_live_grid_value(r, "zone_dependency", v.get()))

    def _save_live_grid_value(self, role, field_name, value):
        target_z = self.active_zone_filter.get()
        target_s = self.active_state_filter.get().lower()
        self.policy_matrix_data[target_z][target_s][role][field_name] = value
        self._redraw_design_map()

    # --- TAB 3: TRANSIT & HARDWARE MONITOR ---
    def _build_transit_terminal_tab(self):
        main_pane = ttk.Frame(self.tab3, padding="5")
        main_pane.pack(fill=tk.BOTH, expand=True)

        left_frame = ttk.LabelFrame(main_pane, text=" Live Plant SCADA Access Monitoring Map ", padding="5")
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.scada_canvas = tk.Canvas(left_frame, bg="#F8F9FA", borderwidth=1, relief="solid")
        self.scada_canvas.pack(fill=tk.BOTH, expand=True)

        right_frame = ttk.Frame(main_pane, width=380)
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        right_frame.pack_propagate(False)

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

        hw_group = ttk.LabelFrame(right_frame, text=" 3. Hardware / Manual Tap Trigger ", padding="10")
        hw_group.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(hw_group, text="Select Role Token to Tap:").pack(anchor="w")
        available_roles = list(self.loader.operational_requirements.keys()) + ["contractor"]
        self.cb_mock_role = ttk.Combobox(hw_group, values=available_roles, state="readonly")
        self.cb_mock_role.set("reactor_operator")
        self.cb_mock_role.pack(fill=tk.X, pady=(2, 10))

        btn_tap = ttk.Button(hw_group, text="  Execute Simulated Badge Scan", command=self.process_simulated_transit, padding=5)
        btn_tap.pack(fill=tk.X)

        log_group = ttk.LabelFrame(right_frame, text=" Terminal Audit Console ", padding="5")
        log_group.pack(fill=tk.BOTH, expand=True)

        self.txt_log = tk.Text(log_group, bg="#212529", fg="#00FF00", font=("Consolas", 9), wrap=tk.WORD)
        self.txt_log.pack(fill=tk.BOTH, expand=True)

        self._render_live_scada_layout()

    def _render_live_scada_layout(self):
        self.scada_canvas.delete("all")
        cy_room = "protected_area_courtyard"
        cy_coords = self.room_coordinates[cy_room]
        cy_zone = self.pm.room_to_zone.get(cy_room, "Zone_1") if self.pm else "Zone_1"
        self.scada_canvas.create_rectangle(
            cy_coords[0], cy_coords[1], cy_coords[2], cy_coords[3],
            fill=self.zone_colors[cy_zone], outline="#6C757D", width=2, dash=(5, 5)
        )
        self.scada_canvas.create_text(cy_coords[0] + 130, cy_coords[3] - 20, text=f"courtyard ({cy_zone})", font=("Helvetica", 9, "bold"), fill="#495057")

        for room in reversed(self.collision_check_order):
            if room == "protected_area_courtyard": continue
            coords = self.room_coordinates[room]
            zone = self.pm.room_to_zone.get(room, "Zone_1") if self.pm else "Zone_1"
            color = self.zone_colors[zone]
            is_vital = room in ["main_control_room", "reactor_containment", "auxiliary_generator_bldg"]
            border_w = 3 if is_vital else 1
            border_c = "#343A40" if is_vital else "#6C757D"
            dash_style = (4, 4) if room == "maintenance_bypass_tunnel" else None

            self.scada_canvas.create_rectangle(
                coords[0], coords[1], coords[2], coords[3],
                fill=color, outline=border_c, width=border_w, dash=dash_style
            )

            display_label = room.replace("_", " ")
            if "corridor" in display_label: display_label = "fuel_service\ncorridor"
            elif "tunnel" in display_label: display_label = "maintenance_bypass\ntunnel"
            elif "generator" in display_label: display_label = "auxiliary_gen\nbldg"
            mid_x = (coords[0] + coords[2]) / 2
            mid_y = (coords[1] + coords[3]) / 2

            if room == "fuel_service_corridor":
                self.scada_canvas.create_text(coords[0] + 80, coords[1] + 18, text=f"{display_label} ({zone})", font=("Helvetica", 9, "bold"), fill="#212529")
            else:
                self.scada_canvas.create_text(mid_x, mid_y, text=f"{display_label}\n({zone})", font=("Helvetica", 8, "bold" if is_vital else "normal"), fill="#212529", justify=tk.CENTER)

        self.scada_canvas.create_line(110, 460, 220, 460, fill="#495057", width=2, dash=(2, 2))
        self.scada_canvas.create_line(110, 180, 200, 180, fill="#495057", width=2, dash=(2, 2))

        for p_coords in self.portal_coordinates:
            self.scada_canvas.create_rectangle(p_coords[0], p_coords[1], p_coords[2], p_coords[3], fill="#212529", outline="#FFFFFF", width=1)

    def process_simulated_transit(self, raw_uid=None):
        if not self.engine:
            messagebox.showwarning("Engine Missing", "Please click 'Compile, Deploy & Hot-Reload Security Policy' at the bottom first!")
            return

        self.scada_canvas.delete("vector_line")
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
        if room == "protected_area_courtyard":
            return (425, 330)
        coords = self.room_coordinates[room]
        return ((coords[0] + coords[2]) / 2, (coords[1] + coords[3]) / 2)

    def _draw_routing_vector_trajectory(self, path_nodes):
        points = [self._get_room_waypoint(room) for room in path_nodes]
        for i in range(len(points) - 1):
            self.scada_canvas.create_line(
                points[i][0], points[i][1], points[i+1][0], points[i+1][1],
                fill="#0056B3", width=4, arrow=tk.LAST, tags="vector_line"
            )
            self.scada_canvas.create_oval(
                points[i][0]-4, points[i][1]-4, points[i][0]+4, points[i][1]+4,
                fill="#00FFF0", outline="#0056B3", width=1, tags="vector_line"
            )

    def _flash_access_feedback_glow(self, is_granted=True):
        flash_color = "#28A745" if is_granted else "#DC3545"
        alert_box = self.scada_canvas.create_rectangle(5, 5, 800, 550, outline=flash_color, width=6)
        self.root.after(400, lambda: self.scada_canvas.delete(alert_box))

    # ------------------------------------------------------------------
    #  DEPLOYMENT & HOT-RELOAD EXECUTION
    # ------------------------------------------------------------------
    def export_and_reload_policy(self):
        author = self.author_entry.get().strip()
        if not author:
            messagebox.showerror("Validation Fault", "Engineer Author Name signature cannot be empty.")
            return

        final_zone_policies = {}
        for zone in self.zones:
            final_zone_policies[zone] = {}
            for state in ["normal", "emergency"]:
                final_zone_policies[zone][state] = {}
                for role in self.roles:
                    live_src = self.policy_matrix_data[zone][state][role]
                    dep = live_src["zone_dependency"]
                    final_zone_policies[zone][state][role] = {
                        "access": live_src["access"],
                        "requires_escort": live_src["requires_escort"],
                        "escort_role": "security_officer" if live_src["requires_escort"] else None,
                        "time_window": [live_src["start_hour"], live_src["end_hour"]],
                        "zone_dependency": None if dep == "None" else dep
                    }

        payload = {
            "author_name": author,
            "room_to_zone": self.room_zone_mapping,
            "zone_policies": final_zone_policies
        }

        try:
            with open(self.policy_path, 'w') as f:
                json.dump(payload, f, indent=2)

            # --- HOT RELOAD ENGINE IN MEMORY ---
            self.pm = PolicyManager(self.policy_path, self.loader)
            self.engine = GraphEngine(self.loader, self.pm)

            # Re-render Tab 3 SCADA layout with active policy colors
            self._render_live_scada_layout()

            messagebox.showinfo("Success & Hot-Reloaded", f"Security Policy compiled and loaded live into memory!\n\nYou can now test hardware taps immediately in Tab 3.")
        except Exception as e:
            messagebox.showerror("Export Fault", f"Failed to export policy: {e}")

if __name__ == "__main__":
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(src_dir)
    b_path = os.path.join(root_dir, "data", "facility_blueprint.json")
    p_path = os.path.join(root_dir, "data", "policy_config.json")

    root_window = tk.Tk()
    app = UnifiedSMRSecurityTerminal(root_window, b_path, p_path)
    root_window.mainloop()