import os
import json
import tkinter as tk
from tkinter import ttk, messagebox
from blueprint_loader import BlueprintLoader

class PolicyDashboardApp:
    def __init__(self, root, blueprint_path, output_path):
        self.root = root
        self.root.title("SMR Physical Protection Access Management Terminal")
        self.root.geometry("1150x750")
        
        self.blueprint_path = blueprint_path
        self.output_path = output_path
        
        # Ingest topography rules dynamically
        self.loader = BlueprintLoader(self.blueprint_path)
        self.rooms = self.loader.get_all_rooms()
        self.roles = list(self.loader.operational_requirements.keys())
        self.zones = ["Zone_1", "Zone_2", "Zone_3", "Zone_4", "Zone_5"]
        self.states = ["Normal", "Emergency"]
        self.access_options = ["Permitted", "Restricted", "Denied"]
        
        # Color mapping palette for visual security gradient tiers
        self.zone_colors = {
            "Zone_1": "#D4EDDA",  # Soft Green
            "Zone_2": "#FFF3CD",  # Soft Yellow
            "Zone_3": "#CCE5FF",  # Soft Blue
            "Zone_4": "#E2D9F3",  # Soft Purple
            "Zone_5": "#F8D7DA"   # Soft Red
        }
        
        # Vertically Compressed Spatial Coordinates Mapping (Safer Y-bounding limits)
        # Format: (x1, y1, x2, y2)
        self.room_coordinates = {
            "protected_area_courtyard": (40, 30, 750, 390),
            "rad_waste_building":        (70, 60, 180, 130),
            "nuclear_receiving":        (220, 50, 390, 130),   # Top side of corridor
            "office_sas_hub":           (440, 290, 610, 370),  # Bottom side of corridor
            "fuel_service_corridor":    (200, 130, 710, 290),  # Centered large spine backbone
            "main_control_room":        (240, 170, 420, 250),  # Encapsulated inside corridor
            "reactor_containment":      (490, 170, 670, 250),  # Encapsulated inside corridor
            "security_gatehouse":       (325, 365, 435, 415),  # Straddles courtyard boundary
            "outer_parking":            (160, 440, 340, 500),  # Shifted safely upward
            "visitor_center":           (380, 440, 520, 500)   # Shifted safely upward
        }
        
        # Priority resolution tracking order for mouse-click collisions
        self.collision_check_order = [
            "main_control_room", "reactor_containment", "fuel_service_corridor",
            "nuclear_receiving", "office_sas_hub", "rad_waste_building",
            "security_gatehouse", "outer_parking", "visitor_center",
            "protected_area_courtyard"
        ]
        
        self.room_zone_mapping = {}
        self.policy_matrix_data = {}
        
        self._initialize_default_policy_data()
        self._build_ui()

    def _initialize_default_policy_data(self):
        """Seed baseline permission attributes to memory arrays."""
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
                    
        # All facility rooms default directly to Zone_1
        for room in self.rooms:
            self.room_zone_mapping[room] = "Zone_1"

    def _build_ui(self):
        main_container = ttk.Frame(self.root, padding="15")
        main_container.pack(fill=tk.BOTH, expand=True)
        
        # Metadata Header Frame
        meta_frame = ttk.LabelFrame(main_container, text=" Configuration Metadata ", padding="10")
        meta_frame.pack(fill=tk.X, pady=(0, 15))
        
        ttk.Label(meta_frame, text="System Engineer Name:").pack(side=tk.LEFT, padx=5)
        self.author_entry = ttk.Entry(meta_frame, width=30)
        self.author_entry.insert(0, "Systems_Engineering_Group_A")
        self.author_entry.pack(side=tk.LEFT, padx=5)

        # Tabbed Layout Notebook
        self.notebook = ttk.Notebook(main_container)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=(0, 10))
        
        self._build_spatial_mapping_tab()
        self._build_policy_matrix_tab()

        # Global Compilation Trigger Control
        deploy_frame = ttk.Frame(main_container)
        deploy_frame.pack(fill=tk.X, side=tk.BOTTOM, pady=5)
        
        btn_deploy = ttk.Button(
            deploy_frame, 
            text="🔒 Compile & Deploy Complete Security Policy Layout", 
            command=self.export_policy_configuration,
            padding="10"
        )
        btn_deploy.pack(fill=tk.X)

    def _build_spatial_mapping_tab(self):
        """Tab 1: Renders the 2D site schematic map canvas interface."""
        tab_frame = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(tab_frame, text=" 1. Interactive Site Layout Map ")
        
        # Interactive Vector Map Panel
        map_wrapper = ttk.LabelFrame(tab_frame, text=" Interactive 2D Plant Floor Plan (Click any room to change Zone assignment) ", padding="10")
        map_wrapper.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.map_canvas = tk.Canvas(map_wrapper, bg="#F8F9FA", borderwidth=1, relief="solid")
        self.map_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Bind left mouse-click button trigger to collision intercept routine
        self.map_canvas.bind("<Button-1>", self._handle_map_click)

        # Right Informational Sidebar Guidance panel
        side_frame = ttk.LabelFrame(tab_frame, text=" Design Instructions ", padding="15", width=320)
        side_frame.pack(side=tk.RIGHT, fill=tk.BOTH, padx=(10, 0))
        side_frame.pack_propagate(False)
        
        guide_text = (
            "Cyber-Physical System Design:\n\n"
            "• Click directly on any room on the physical blueprint to alter its logic Zone perimeter tier.\n\n"
            "• Outer Protected Area Fence is marked by a thick dashed border line.\n\n"
            "• The Main Control Room and Reactor Containment reside inside the Fuel Service Corridor backbone, separating them from the open courtyard."
        )
        ttk.Label(side_frame, text=guide_text, justify=tk.LEFT, wraplength=290).pack(anchor="n")
        
        # Initial canvas render processing
        self._redraw_facility_map()

    def _redraw_facility_map(self):
        """Clears and re-renders the 2D vector graphic plan from active data matrices."""
        self.map_canvas.delete("all")
        
        # Render the Protected Area Courtyard background and outer boundary fence first
        cy_room = "protected_area_courtyard"
        cy_coords = self.room_coordinates[cy_room]
        cy_zone = self.room_zone_mapping[cy_room]
        cy_color = self.zone_colors[cy_zone]
        
        # Draw courtyard fill block
        self.map_canvas.create_rectangle(
            cy_coords[0], cy_coords[1], cy_coords[2], cy_coords[3],
            fill=cy_color, outline="#6C757D", width=2, dash=(5, 5)
        )
        # Position courtyard text label away from internal buildings
        self.map_canvas.create_text(
            cy_coords[0] + 130, cy_coords[3] - 20,
            text=f"protected_area_courtyard ({cy_zone})", font=("Helvetica", 9, "bold"), fill="#495057"
        )
        
        # Enumerate remaining spatial structures in correct rendering sequence
        for room in reversed(self.collision_check_order):
            if room == "protected_area_courtyard":
                continue # Handled as baseline layer
                
            coords = self.room_coordinates[room]
            zone = self.room_zone_mapping[room]
            color = self.zone_colors[zone]
            
            # Use thick double borders for high-value vital asset cells
            is_vital = room in ["main_control_room", "reactor_containment"]
            border_w = 3 if is_vital else 1
            border_c = "#343A40" if is_vital else "#6C757D"
            
            # Draw structural boundary room cell block
            self.map_canvas.create_rectangle(
                coords[0], coords[1], coords[2], coords[3],
                fill=color, outline=border_c, width=border_w
            )
            
            # Format display label text string
            display_label = room.replace("_", " ")
            if len(display_label) > 18:
                display_label = display_label.replace(" building", "\nbldg").replace(" corridor", "\ncorridor")
            
            # Reposition the Fuel Service Corridor label to avoid overlap with its internal rooms
            if room == "fuel_service_corridor":
                self.map_canvas.create_text(
                    coords[0] + 110, coords[1] + 18,
                    text=f"{display_label} ({zone})",
                    font=("Helvetica", 9, "bold"),
                    fill="#212529", justify=tk.LEFT
                )
            else:
                # Calculate geometric midpoint center coordinate for text injection
                mid_x = (coords[0] + coords[2]) / 2
                mid_y = (coords[1] + coords[3]) / 2
                
                self.map_canvas.create_text(
                    mid_x, mid_y,
                    text=f"{display_label}\n({zone})",
                    font=("Helvetica", 9, "bold" if is_vital else "normal"),
                    fill="#212529", justify=tk.CENTER
                )

    def _handle_map_click(self, event):
        """Intercepts click coordinates and resolves spatial box collisions."""
        click_x, click_y = event.x, event.y
        detected_room = None
        
        # Trace priority check order sequence to resolve nested background bounds overlapping correctly
        for room in self.collision_check_order:
            coords = self.room_coordinates[room]
            if coords[0] <= click_x <= coords[2] and coords[1] <= click_y <= coords[3]:
                detected_room = room
                break
                
        if detected_room:
            self._spawn_zone_popup_menu(event, detected_room)

    def _spawn_zone_popup_menu(self, event, room_name):
        """Constructs a context dropdown menu at the mouse click location."""
        popup = tk.Menu(self.root, tearoff=0)
        
        for zone in self.zones:
            popup.add_command(
                label=f"Assign to {zone}", 
                command=lambda z=zone, r=room_name: self._update_room_zone(r, z)
            )
            
        popup.post(event.x_root, event.y_root)

    def _update_room_zone(self, room_name, target_zone):
        """Syncs the selection to data structures and triggers a map refresh."""
        self.room_zone_mapping[room_name] = target_zone
        self._redraw_facility_map()

    def _build_policy_matrix_tab(self):
        """Tab 2: Controls rule definitions and conditional constraints."""
        tab_frame = ttk.Frame(self.notebook, padding="15")
        self.notebook.add(tab_frame, text=" 2. Access Control Permissions Matrix ")
        
        selector_frame = ttk.Frame(tab_frame, padding="5")
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

        self.matrix_wrapper = ttk.LabelFrame(tab_frame, text=" Role-Based Clearances Configuration ", padding="10")
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

    def export_policy_configuration(self):
        author = self.author_entry.get().strip()
        if not author:
            messagebox.showerror("Validation Fault", "System Engineer Author Name signature cannot be empty.")
            return
            
        room_assignments = self.room_zone_mapping
        
        final_zone_policies = {}
        for zone in self.zones:
            final_zone_policies[zone] = {}
            for state in ["normal", "emergency"]:
                final_zone_policies[zone][state] = {}
                for role in self.roles:
                    live_src = self.policy_matrix_data[zone][state][role]
                    dep = live_src["zone_dependency"]
                    normalized_dep = None if dep == "None" else dep
                    
                    final_zone_policies[zone][state][role] = {
                        "access": live_src["access"],
                        "requires_escort": live_src["requires_escort"],
                        "escort_role": "security_officer" if live_src["requires_escort"] else None,
                        "time_window": [live_src["start_hour"], live_src["end_hour"]],
                        "zone_dependency": normalized_dep
                    }
                    
        payload = {
            "author_name": author,
            "room_to_zone": room_assignments,
            "zone_policies": final_zone_policies
        }
        
        try:
            with open(self.output_path, 'w') as f:
                json.dump(payload, f, indent=2)
            messagebox.showinfo("Success", f"Security Framework compiled and written to:\n{self.output_path}")
        except Exception as e:
            messagebox.showerror("IO Write Error", f"Could not export policy schema: {e}")


if __name__ == "__main__":
    src_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(src_dir)
    
    b_path = os.path.join(root_dir, "data", "facility_blueprint.json")
    p_path = os.path.join(root_dir, "data", "policy_config.json")
    
    root_window = tk.Tk()
    app = PolicyDashboardApp(root_window, b_path, p_path)
    root_window.mainloop()