import math
import unreal


"""
Run inside Unreal Editor Python or with:
UnrealEditor-Cmd.exe ExtractionGame.uproject -ExecutePythonScript=...

This script creates/saves /Game/Maps/LV_Extraction and builds a 100m x 100m
blockout map for the theme "Tide-Eroded Wasteland / Submerged Old Port".

It uses basic cubes plus existing project blueprints when available:
- /Game/Blueprints/interact/BP_Chest
- /Game/Blueprints/Enemy/BP_Monster
- /Game/Blueprints/interact/BP_ExitDoor
"""


actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
asset_lib = unreal.EditorAssetLibrary


def load(path):
    return asset_lib.load_asset(path)


CUBE = load("/Engine/BasicShapes/Cube.Cube")
MAP_PACKAGE = "/Game/Maps/LV_Extraction"
MATERIAL_DIR = "/Game/Materials"
GENERATED_PREFIXES = (
    "BLOCKOUT_",
    "Sea_",
    "WaterSlow_",
    "Dock_",
    "Boat_",
    "Container_",
    "Foundation_",
    "House_",
    "Window_",
    "Door_",
    "SecondFloor_",
    "PathBridge_",
    "Underground_",
    "Helipad_",
    "Heli_",
    "SignalFlare_",
    "Guardian_",
    "OldVault_",
    "East_Ruined_",
    "Upper_",
    "SignalTower_",
    "Stair_",
    "Ramp_",
    "BrokenWall_",
    "BrokenBridge_",
    "ChestPoint_",
    "MonsterSpawn_",
    "ExitDoor_",
    "Label_",
    "NavMeshBoundsVolume_",
)


def make_material(name, color, opacity=1.0):
    if not asset_lib.does_directory_exist(MATERIAL_DIR):
        asset_lib.make_directory(MATERIAL_DIR)

    path = f"{MATERIAL_DIR}/{name}"
    existing = load(path)
    if existing:
        return existing

    asset_tools = unreal.AssetToolsHelpers.get_asset_tools()
    mat = asset_tools.create_asset(name, MATERIAL_DIR, unreal.Material, unreal.MaterialFactoryNew())
    if not mat:
        return None

    base = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant3Vector, -400, 0
    )
    base.constant = unreal.LinearColor(color[0], color[1], color[2], 1.0)
    unreal.MaterialEditingLibrary.connect_material_property(
        base, "", unreal.MaterialProperty.MP_BASE_COLOR
    )

    rough = unreal.MaterialEditingLibrary.create_material_expression(
        mat, unreal.MaterialExpressionConstant, -400, 160
    )
    rough.r = 0.85
    unreal.MaterialEditingLibrary.connect_material_property(
        rough, "", unreal.MaterialProperty.MP_ROUGHNESS
    )

    if opacity < 1.0:
        mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property("two_sided", True)
        alpha = unreal.MaterialEditingLibrary.create_material_expression(
            mat, unreal.MaterialExpressionConstant, -400, 320
        )
        alpha.r = opacity
        unreal.MaterialEditingLibrary.connect_material_property(
            alpha, "", unreal.MaterialProperty.MP_OPACITY
        )

    unreal.MaterialEditingLibrary.layout_material_expressions(mat)
    unreal.MaterialEditingLibrary.recompile_material(mat)
    asset_lib.save_asset(path)
    return mat


def get_materials():
    return {
        "ground": make_material("M_Blockout_Ground_Grey", (0.42, 0.42, 0.40)),
        "water": make_material("M_Blockout_Water_Blue", (0.02, 0.23, 0.92), 0.65),
        "sea": make_material("M_Blockout_Sea_Blue", (0.0, 0.12, 0.56), 0.75),
        "dock": make_material("M_Blockout_Dock_DarkGrey", (0.22, 0.22, 0.22)),
        "house": make_material("M_Blockout_House_LightGrey", (0.62, 0.62, 0.58)),
        "vault": make_material("M_Blockout_Vault_MetalGrey", (0.32, 0.34, 0.36)),
        "underground": make_material("M_Blockout_Underground_BlueGrey", (0.18, 0.23, 0.30)),
        "container": make_material("M_Blockout_Container_Rust", (0.54, 0.24, 0.12)),
        "helipad": make_material("M_Blockout_Helipad_Yellow", (0.86, 0.63, 0.16)),
        "signal": make_material("M_Blockout_Signal_White", (0.85, 0.85, 0.78)),
    }


def ensure_level():
    if not asset_lib.does_directory_exist("/Game/Maps"):
        asset_lib.make_directory("/Game/Maps")

    if asset_lib.does_asset_exist(MAP_PACKAGE):
        level_subsystem.load_level(MAP_PACKAGE)
    else:
        level_subsystem.new_level(MAP_PACKAGE)


def clear_generated_actors():
    for actor in actor_subsystem.get_all_level_actors():
        label = actor.get_actor_label()
        if label.startswith(GENERATED_PREFIXES):
            actor_subsystem.destroy_actor(actor)


def spawn_cube(label, loc, scale, rot=(0, 0, 0)):
    actor = actor_subsystem.spawn_actor_from_class(
        unreal.StaticMeshActor,
        unreal.Vector(*loc),
        unreal.Rotator(rot[0], rot[1], rot[2]),
    )
    actor.set_actor_label(label)
    actor.static_mesh_component.set_static_mesh(CUBE)
    actor.set_actor_scale3d(unreal.Vector(*scale))
    return actor


def spawn_window_marker(label, loc, scale, rot=(0, 0, 0)):
    # Thin dark blue/grey cubes used as readable window holes on greybox walls.
    actor = spawn_cube(label, loc, scale, rot)
    return actor


def spawn_ruined_house(prefix, loc, size=(9, 8), floors=1, yaw=0):
    x, y, z = loc
    sx, sy = size
    height = 260 * floors
    wall_z = z + height / 2
    roof_z = z + height + 18

    spawn_cube(f"{prefix}_Foundation", (x, y, z - 15), (sx + 1.2, sy + 1.2, 0.3), (0, 0, yaw))
    # Build walls in segments so ruins have doors and readable broken openings.
    spawn_cube(f"{prefix}_BackWall_Left", (x - sx * 22, y + sy * 50, wall_z), (sx * 0.42, 0.35, height / 100), (0, 0, yaw))
    spawn_cube(f"{prefix}_BackWall_Right", (x + sx * 22, y + sy * 50, wall_z), (sx * 0.42, 0.35, height / 100), (0, 0, yaw))
    spawn_cube(f"{prefix}_LeftWall_A", (x - sx * 50, y - sy * 22, wall_z), (0.35, sy * 0.42, height / 100), (0, 0, yaw))
    spawn_cube(f"{prefix}_LeftWall_B", (x - sx * 50, y + sy * 22, wall_z), (0.35, sy * 0.42, height / 100), (0, 0, yaw))
    spawn_cube(f"{prefix}_RightWall_A", (x + sx * 50, y - sy * 22, wall_z), (0.35, sy * 0.42, height / 100), (0, 0, yaw))
    spawn_cube(f"{prefix}_RightWall_B", (x + sx * 50, y + sy * 22, wall_z), (0.35, sy * 0.42, height / 100), (0, 0, yaw))
    spawn_cube(f"{prefix}_FrontWall_Left", (x - sx * 32, y - sy * 50, wall_z), (sx * 0.25, 0.35, height / 100), (0, 0, yaw))
    spawn_cube(f"{prefix}_FrontWall_Right", (x + sx * 32, y - sy * 50, wall_z), (sx * 0.25, 0.35, height / 100), (0, 0, yaw))
    spawn_window_marker(f"Window_{prefix}_Back", (x, y + sy * 50 - 8, wall_z + 40), (1.25, 0.08, 0.75), (0, 0, yaw))
    spawn_window_marker(f"Window_{prefix}_Left", (x - sx * 50 + 8, y, wall_z + 35), (0.08, 1.25, 0.75), (0, 0, yaw))
    spawn_window_marker(f"Window_{prefix}_Right", (x + sx * 50 - 8, y, wall_z + 35), (0.08, 1.25, 0.75), (0, 0, yaw))
    spawn_window_marker(f"Door_{prefix}_Front", (x, y - sy * 50 - 8, z + 100), (1.6, 0.08, 1.8), (0, 0, yaw))

    if floors >= 2:
        spawn_cube(f"SecondFloor_{prefix}_Slab", (x, y, z + 285), (sx + 0.35, sy + 0.35, 0.25), (0, 0, yaw))
        # Exterior access stairs to make multi-story buildings actually usable.
        for i in range(10):
            spawn_cube(
                f"SecondFloor_{prefix}_Stair_{i+1:02d}",
                (x - sx * 80 + i * 70, y - sy * 50 - 120, z + 15 + i * 28),
                (1.2, 1.1, 0.28),
                (0, 0, yaw),
            )

    # Broken upper slab/roof reads as ruin while still giving cover.
    spawn_cube(f"{prefix}_RoofSlab", (x, y, roof_z), (sx * 0.65, sy + 0.8, 0.28), (0, 0, yaw))


def spawn_bp(label, asset_path, loc, rot=(0, 0, 0)):
    asset = load(asset_path)
    if not asset:
        unreal.log_warning(f"Missing asset: {asset_path}. Skipped {label}.")
        return None
    cls = asset.generated_class()
    actor = actor_subsystem.spawn_actor_from_class(
        cls,
        unreal.Vector(*loc),
        unreal.Rotator(rot[0], rot[1], rot[2]),
    )
    actor.set_actor_label(label)
    return actor


def spawn_text(label, text, loc, scale=2.0):
    actor = actor_subsystem.spawn_actor_from_class(
        unreal.TextRenderActor,
        unreal.Vector(*loc),
        unreal.Rotator(0, 180, 0),
    )
    actor.set_actor_label(label)
    comp = actor.get_component_by_class(unreal.TextRenderComponent)
    comp.set_text(text)
    comp.set_world_size(80 * scale)
    return actor


def spawn_water_slow_volume(label, source_actor):
    loc = source_actor.get_actor_location()
    scale = source_actor.get_actor_scale3d()
    loc.z = loc.z + 120
    actor = actor_subsystem.spawn_actor_from_class(
        unreal.TriggerBox,
        loc,
        unreal.Rotator(0, 0, 0),
    )
    actor.set_actor_label(label)
    actor.set_actor_scale3d(unreal.Vector(scale.x, scale.y, 2.4))
    actor.tags = [unreal.Name("WaterSlow")]
    return actor


def apply_visuals_and_water_volumes():
    mats = get_materials()
    water_labels = []

    for actor in actor_subsystem.get_all_level_actors():
        label = actor.get_actor_label()
        comp = actor.get_component_by_class(unreal.StaticMeshComponent)
        if not comp:
            continue

        material = None
        if label.startswith("Sea_"):
            material = mats["sea"]
            water_labels.append(label)
            loc = actor.get_actor_location()
            loc.z = 4 if "OpenWater" in label else 8
            actor.set_actor_location(loc, False, False)
            scale = actor.get_actor_scale3d()
            scale.z = 0.04
            actor.set_actor_scale3d(scale)
        elif label.startswith("BLOCKOUT_ShallowWater") or label.startswith("BLOCKOUT_SubmergedDockWater"):
            material = mats["water"]
            water_labels.append(label)
            loc = actor.get_actor_location()
            loc.z = 8
            actor.set_actor_location(loc, False, False)
            scale = actor.get_actor_scale3d()
            scale.z = 0.04
            actor.set_actor_scale3d(scale)
        elif label.startswith("BLOCKOUT_Ground"):
            material = mats["ground"]
        elif label.startswith("Dock_") or label.startswith("Upper_") or label.startswith("Stair_"):
            material = mats["dock"]
        elif label.startswith("Foundation_") or label.startswith("House_") or label.startswith("East_Ruined_"):
            material = mats["house"]
        elif label.startswith("Window_") or label.startswith("Door_"):
            material = mats["underground"]
        elif label.startswith("OldVault_") or label.startswith("BrokenWall_") or label.startswith("BrokenBridge_") or label.startswith("Boat_") or label.startswith("Guardian_"):
            material = mats["vault"]
        elif label.startswith("Underground_"):
            material = mats["water"] if "Water" in label else mats["underground"]
            if "Water" in label:
                water_labels.append(label)
        elif label.startswith("Container_"):
            material = mats["container"]
        elif label.startswith("Helipad_") or label.startswith("Heli_"):
            material = mats["helipad"]
        elif label.startswith("PathBridge_") or label.startswith("SecondFloor_"):
            material = mats["dock"]
        elif label.startswith("SignalTower_"):
            material = mats["signal"]

        if material:
            comp.set_material(0, material)

    for label in water_labels:
        actor = next((a for a in actor_subsystem.get_all_level_actors() if a.get_actor_label() == label), None)
        if actor:
            spawn_water_slow_volume(f"WaterSlow_{label}", actor)


def build_blockout():
    ensure_level()
    clear_generated_actors()

    # Sea surrounding the playable island. Kept below ground level so the
    # playable floor remains visible and walkable.
    spawn_cube("Sea_North_OpenWater", (0, 6900, -70), (130, 38, 0.2))
    spawn_cube("Sea_South_OpenWater", (0, -6900, -70), (130, 38, 0.2))
    spawn_cube("Sea_West_OpenWater", (-6900, 0, -70), (38, 100, 0.2))
    spawn_cube("Sea_East_OpenWater", (6900, 0, -70), (38, 100, 0.2))
    spawn_cube("Sea_Harbor_Basin", (0, -4550, -30), (82, 15, 0.2))

    # Main 100m x 100m ground. UE cube is 100cm, so scale 100 gives 10000cm.
    spawn_cube("BLOCKOUT_Ground_100m_x_100m", (0, 0, -50), (100, 100, 1))

    # Shallow water channels and submerged streets.
    spawn_cube("BLOCKOUT_ShallowWater_EastStreet", (2600, 500, -20), (18, 75, 0.18))
    spawn_cube("BLOCKOUT_ShallowWater_CentralCanal", (-500, 500, -15), (12, 90, 0.15), (0, 0, 12))
    spawn_cube("BLOCKOUT_SubmergedDockWater", (0, -4300, -15), (70, 12, 0.15))
    spawn_cube("Sea_Breach_WestCanal", (-4700, 900, -22), (10, 42, 0.18), (0, 0, -8))
    spawn_cube("Sea_Breach_EastCanal", (4650, -800, -22), (10, 50, 0.18), (0, 0, 10))

    # South landing dock and broken boat silhouette.
    spawn_cube("Dock_Main_Platform", (0, -3900, 25), (28, 8, 1))
    spawn_cube("Dock_Left_Walkway", (-2100, -3550, 40), (14, 4, 1))
    spawn_cube("Dock_Right_Walkway", (2100, -3550, 40), (14, 4, 1))
    spawn_cube("Dock_Concrete_SeaWall", (0, -4950, 75), (92, 1.2, 1.5))
    spawn_cube("Dock_Left_SeaWall", (-5050, -1200, 75), (1.2, 70, 1.5))
    spawn_cube("Dock_Right_SeaWall", (5050, 200, 75), (1.2, 58, 1.5))
    spawn_cube("Boat_Wreck_Hull", (-2800, -4300, 70), (9, 3, 1.2), (0, 0, -18))

    # Foundations and ruined houses around the old port.
    foundation_data = [
        ("Foundation_SouthMarket", (-1500, -2600, 15), (18, 10, 0.3), 0),
        ("Foundation_CustomsOffice", (1550, -2450, 15), (16, 12, 0.3), 0),
        ("Foundation_CentralSquare", (0, 450, 12), (28, 22, 0.25), 8),
        ("Foundation_EastBlocks", (3500, 1200, 14), (18, 34, 0.3), 0),
        ("Foundation_WestBankPlaza", (-3600, 600, 12), (22, 28, 0.25), 0),
    ]
    for label, loc, scale, yaw in foundation_data:
        spawn_cube(label, loc, scale, (0, 0, yaw))

    spawn_ruined_house("House_SouthMarket_A", (-1750, -2700, 40), (7, 6), 2, 0)
    spawn_ruined_house("House_SouthMarket_B", (-650, -2650, 40), (6, 5), 1, 7)
    spawn_ruined_house("House_CustomsOffice", (1600, -2500, 40), (9, 7), 2, -4)
    spawn_ruined_house("House_Central_Ruins", (-250, 550, 35), (8, 7), 2, 8)
    spawn_ruined_house("House_West_BankAnnex", (-3300, -350, 35), (8, 7), 2, 0)
    spawn_ruined_house("House_East_Apartment_A", (3000, 1500, 45), (7, 6), 2, 0)
    spawn_ruined_house("House_East_Apartment_B", (4300, 150, 45), (7, 6), 2, 0)
    spawn_ruined_house("House_North_ControlRoom", (-450, 2950, 560), (7, 5), 2, 0)

    # Central container maze / cover.
    container_positions = [
        (-1800, -800, 100, 0), (-900, -400, 100, 90), (200, -900, 100, 0),
        (1000, -300, 100, 90), (1750, 500, 100, 0), (-1700, 900, 100, 90),
        (-300, 1200, 100, 0), (900, 1300, 100, 0),
    ]
    for i, (x, y, z, yaw) in enumerate(container_positions, start=1):
        spawn_cube(f"Container_{i:02d}", (x, y, z), (8, 3, 2), (0, 0, yaw))

    # West vault / old bank ruins.
    spawn_cube("OldVault_BackWall", (-4200, 600, 180), (2, 20, 3.6))
    spawn_cube("OldVault_LeftWall_A", (-3600, -820, 180), (8, 2, 3.6))
    spawn_cube("OldVault_LeftWall_B", (-4200, -820, 180), (4, 2, 3.6))
    spawn_cube("OldVault_RightWall_A", (-3600, 2020, 180), (8, 2, 3.6))
    spawn_cube("OldVault_RightWall_B", (-4200, 2020, 180), (4, 2, 3.6))
    spawn_cube("OldVault_Gate_Left", (-2700, 260, 140), (2, 2.4, 2.8))
    spawn_cube("OldVault_Gate_Right", (-2700, 940, 140), (2, 2.4, 2.8))

    # East submerged district ruins.
    for i, y in enumerate([-2200, -900, 400, 1700], start=1):
        spawn_cube(f"East_Ruined_Building_{i}", (3800, y, 220), (7, 7, 4.4))
        spawn_cube(f"East_Ruined_Roof_{i}", (3800, y, 470), (8, 8, 0.5))
        spawn_cube(f"East_Ruined_Foundation_{i}", (3800, y, 18), (10, 10, 0.35))

    # Underground layer: Tide-Eroded Vault. The roof sits low enough to read as
    # underground, while leaving more than two character heights of playable
    # space between floor and ceiling.
    spawn_cube("Underground_VaultFloor_Main", (-2850, 500, -620), (34, 28, 0.6))
    spawn_cube("Underground_VaultCeiling_Main", (-2850, 500, -165), (34, 28, 0.45))
    spawn_cube("Underground_Vault_BackWall", (-4550, 500, -390), (0.6, 20, 4.6))
    spawn_cube("Underground_Vault_LeftWall_A", (-3500, -900, -390), (18, 0.6, 4.6))
    spawn_cube("Underground_Vault_LeftWall_B", (-1750, -900, -390), (10, 0.6, 4.6))
    spawn_cube("Underground_Vault_RightWall_A", (-3500, 1900, -390), (18, 0.6, 4.6))
    spawn_cube("Underground_Vault_RightWall_B", (-1750, 1900, -390), (10, 0.6, 4.6))
    spawn_cube("Underground_Vault_GoldRoom", (-4050, 500, -370), (10, 12, 3.8))
    spawn_cube("Underground_Drainage_Corridor", (-900, -400, -620), (40, 7, 0.55), (0, 0, 8))
    spawn_cube("Underground_Drainage_Water", (-900, -400, -585), (38, 5, 0.15), (0, 0, 8))
    spawn_cube("Underground_ServiceRoom", (900, -1100, -610), (18, 14, 0.5))
    spawn_cube("Underground_ServiceRoom_BackWall", (900, -400, -380), (18, 0.5, 4.4))
    spawn_cube("Underground_ServiceRoom_LeftWall", (0, -1100, -380), (0.5, 14, 4.4))
    spawn_cube("Underground_ServiceRoom_RightWall", (1800, -1100, -380), (0.5, 14, 4.4))

    # Two broad ramp connections between surface and underground. Ramps are
    # easier for the character capsule and AI than tightly stacked steps.
    spawn_cube("Ramp_Underground_WestVault_Access", (-3000, -520, -260), (8, 18, 0.35), (0, -22, 6))
    spawn_cube("Ramp_Underground_WestVault_Landing_Surface", (-3150, -1280, 35), (9, 5, 0.35), (0, 0, 6))
    spawn_cube("Ramp_Underground_WestVault_Landing_Bottom", (-2850, 180, -585), (10, 6, 0.35), (0, 0, 6))
    spawn_cube("Ramp_Underground_CentralDrain_Access", (250, -1500, -250), (8, 22, 0.35), (0, 24, -10))
    spawn_cube("Ramp_Underground_CentralDrain_Landing_Surface", (900, -2550, 35), (9, 5, 0.35), (0, 0, -10))
    spawn_cube("Ramp_Underground_CentralDrain_Landing_Bottom", (-300, -560, -585), (10, 6, 0.35), (0, 0, -10))

    # North upper platform and stairs. Height is now clearly above the ground,
    # with more than two human-model heights between layers.
    spawn_cube("Upper_Platform_North", (0, 3700, 520), (40, 18, 1))
    spawn_cube("Upper_Platform_LowerLanding", (-1700, 1750, 250), (13, 9, 0.8))
    spawn_cube("SignalTower_Base", (2800, 3700, 650), (4, 4, 3))
    spawn_cube("SignalTower_Mast", (2800, 3700, 1200), (1, 1, 9))

    # Wide, shallow staircase to second layer.
    for i in range(23):
        spawn_cube(
            f"Stair_To_Upper_{i+1:02d}",
            (-1700, 1450 + i * 115, 12.5 + i * 25),
            (8.0, 1.55, 0.25),
        )
    spawn_cube("Stair_Left_GuideWall", (-2180, 2700, 275), (0.45, 30, 1.4))
    spawn_cube("Stair_Right_GuideWall", (-1220, 2700, 275), (0.45, 30, 1.4))

    # Third layer: helicopter extraction pad. Only one narrow route connects
    # second layer to third layer, guarded by a strong monster.
    spawn_cube("Helipad_Platform_ThirdLayer", (2500, 4550, 1120), (16, 16, 0.8))
    spawn_cube("Helipad_Marking_Cross_A", (2500, 4550, 1168), (10, 1, 0.12))
    spawn_cube("Helipad_Marking_Cross_B", (2500, 4550, 1170), (1, 10, 0.12))
    spawn_cube("SignalTower_Heli_Base", (2050, 5000, 1240), (3.2, 3.2, 2.4))
    spawn_cube("SignalTower_Heli_Mast", (2050, 5000, 1650), (0.7, 0.7, 6.0))
    spawn_cube("SignalTower_Heli_Antenna_A", (2050, 5000, 1870), (0.25, 5.5, 0.18), (0, 0, 18))
    spawn_cube("SignalTower_Heli_Antenna_B", (2050, 5000, 1905), (5.5, 0.25, 0.18), (0, 0, -18))
    spawn_cube("SignalFlare_LaunchTube", (2280, 4700, 1225), (0.45, 0.45, 2.0), (0, 0, 20))
    spawn_cube("SignalFlare_RedMarker", (2280, 4700, 1370), (0.9, 0.9, 0.35), (0, 0, 20))
    spawn_cube("Helipad_CallZone_PaidExtraction", (2500, 4550, 1176), (5.5, 5.5, 0.08))
    spawn_cube("Heli_Wreck_Body", (3150, 4550, 1240), (5, 1.8, 1.2), (0, 0, 8))
    spawn_cube("Heli_Wreck_Tail", (3750, 4550, 1245), (6, 0.45, 0.45), (0, 0, 8))
    spawn_cube("Heli_Wreck_Rotor", (3150, 4550, 1340), (0.4, 8, 0.08), (0, 0, 8))
    spawn_cube("Ramp_Helipad_SingleAccess_FromSecond", (1650, 4100, 800), (20, 3.2, 0.45), (0, 18, -10))
    spawn_cube("Ramp_Helipad_Landing_SecondLayer", (760, 3900, 560), (8, 5, 0.35), (0, 0, -10))
    spawn_cube("Ramp_Helipad_Landing_ThirdLayer", (2420, 4520, 1125), (9, 5, 0.35), (0, 0, -10))
    spawn_cube("Helipad_NarrowBridge", (1900, 4280, 980), (15, 3.2, 0.45), (0, 0, -10))
    spawn_cube("Guardian_Gate_LeftPillar", (1540, 4050, 930), (0.55, 0.55, 2.6))
    spawn_cube("Guardian_Gate_RightPillar", (1540, 4510, 930), (0.55, 0.55, 2.6))

    # Extra upper-level routes between ruined buildings. The third layer still
    # has only one access route, but the lower ruins now have multiple playable
    # elevated paths.
    spawn_cube("PathBridge_SouthMarket_To_Customs", (-200, -2500, 345), (18, 2.2, 0.35))
    spawn_cube("PathBridge_Central_To_East", (1850, 900, 345), (22, 2.2, 0.35), (0, 0, 12))
    spawn_cube("PathBridge_Central_To_WestBank", (-1850, 450, 340), (20, 2.2, 0.35), (0, 0, -6))
    spawn_cube("PathBridge_North_Control_To_Platform", (-250, 3350, 840), (16, 2.4, 0.35), (0, 0, 4))
    spawn_cube("SecondFloor_Railing_SouthBridge_L", (-200, -2360, 430), (18, 0.25, 1.1))
    spawn_cube("SecondFloor_Railing_SouthBridge_R", (-200, -2640, 430), (18, 0.25, 1.1))

    # Broken walls as navigation blockers.
    wall_data = [
        ("BrokenWall_SouthCenter_Left", (-1500, -2100, 140), (9, 1, 2.8), 0),
        ("BrokenWall_SouthCenter_Right", (1500, -2100, 140), (9, 1, 2.8), 0),
        ("BrokenWall_WestCenter_A", (-2500, -1500, 140), (1, 8, 2.8), 0),
        ("BrokenWall_WestCenter_B", (-2500, 500, 140), (1, 8, 2.8), 0),
        ("BrokenWall_EastCenter_A", (2400, 1100, 140), (1, 8, 2.8), 0),
        ("BrokenWall_EastCenter_B", (2400, 2700, 140), (1, 6, 2.8), 0),
        ("BrokenBridge_NorthGap_Left", (-1900, 2450, 160), (7, 2, 1.2), 10),
        ("BrokenBridge_NorthGap_Right", (-450, 2450, 160), (7, 2, 1.2), 10),
    ]
    for label, loc, scale, yaw in wall_data:
        spawn_cube(label, loc, scale, (0, 0, yaw))

    # Gameplay points.
    chest_path = "/Game/Blueprints/interact/BP_Chest.BP_Chest"
    monster_path = "/Game/Blueprints/Enemy/BP_Monster.BP_Monster"
    exit_path = "/Game/Blueprints/interact/BP_ExitDoor.BP_ExitDoor"

    chest_points = [
        (-900, -3500, 100), (1250, -3450, 100), (-2100, -1200, 100),
        (-350, -250, 100), (1400, 250, 100), (-3950, 600, 100),
        (-2800, 1550, 100), (3450, -2100, 100), (3450, 700, 100),
        (300, 3650, 590),
        (-4050, 500, -520), (-2800, 1600, -520), (800, -1050, -510),
        (-900, -400, -510), (2450, 4550, 1200), (2900, 4300, 1200),
    ]
    for i, loc in enumerate(chest_points, start=1):
        spawn_bp(f"ChestPoint_{i:02d}", chest_path, loc)

    monster_points = [
        (0, -1200, 120), (-3300, 900, 120), (3100, -700, 120),
        (-800, 2300, 120), (2100, 3300, 590),
        (-3950, 400, -500), (-1200, -450, -500), (900, -1100, -500),
        (1620, 4260, 930),
    ]
    for i, loc in enumerate(monster_points, start=1):
        monster = spawn_bp(f"MonsterSpawn_{i:02d}", monster_path, loc)
        if i == len(monster_points) and monster:
            monster.set_actor_label("Guardian_StrongMonster_HelipadAccess")
            monster.set_actor_scale3d(unreal.Vector(1.8, 1.8, 1.8))

    exit_points = [
        (3200, -3950, 120),
        (2500, 4550, 1230),
    ]
    for i, loc in enumerate(exit_points, start=1):
        spawn_bp(f"ExitDoor_{i:02d}", exit_path, loc)

    # Labels for orientation.
    spawn_text("Label_MapTitle", "Submerged Old Port", (0, -5000, 350), 2.2)
    spawn_text("Label_WestVault", "Old Vault", (-4100, 2200, 350), 1.2)
    spawn_text("Label_EastRuins", "Submerged District", (3500, 2600, 350), 1.2)
    spawn_text("Label_SignalTower", "Signal Tower", (2400, 4300, 850), 1.1)
    spawn_text("Label_HelicopterPaidExit", "Signal Flare Helicopter Exit: Cost 50 Gold", (2500, 5200, 1500), 1.0)
    spawn_text("Label_DockExit", "Dock Exit", (3200, -4500, 300), 1.1)

    # NavMeshBoundsVolume. Scale may need manual adjustment in editor.
    nav = actor_subsystem.spawn_actor_from_class(
        unreal.NavMeshBoundsVolume,
        unreal.Vector(0, 0, 500),
        unreal.Rotator(0, 0, 0),
    )
    nav.set_actor_label("NavMeshBoundsVolume_100m")
    nav.set_actor_scale3d(unreal.Vector(100, 100, 10))

    apply_visuals_and_water_volumes()

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("Submerged Old Port blockout complete. Press P to inspect NavMesh.")


build_blockout()
