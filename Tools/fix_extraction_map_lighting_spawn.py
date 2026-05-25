import unreal


MAP_PACKAGE = "/Game/Maps/LV_Extraction"

actor_subsystem = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
level_subsystem = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
asset_lib = unreal.EditorAssetLibrary


def destroy_by_labels(prefixes):
    for actor in actor_subsystem.get_all_level_actors():
        if actor.get_actor_label().startswith(prefixes):
            actor_subsystem.destroy_actor(actor)


def spawn_actor(cls, label, loc, rot=(0, 0, 0)):
    actor = actor_subsystem.spawn_actor_from_class(
        cls,
        unreal.Vector(*loc),
        unreal.Rotator(rot[0], rot[1], rot[2]),
    )
    actor.set_actor_label(label)
    return actor


def main():
    if not asset_lib.does_asset_exist(MAP_PACKAGE):
        raise RuntimeError(f"Missing map: {MAP_PACKAGE}")

    level_subsystem.load_level(MAP_PACKAGE)

    destroy_by_labels((
        "GAMEPLAY_PlayerStart",
        "LIGHT_",
        "ENV_",
    ))

    # Player starts on the south dock. Z is high enough for the capsule to land
    # on the dock instead of spawning inside it.
    spawn_actor(
        unreal.PlayerStart,
        "GAMEPLAY_PlayerStart_Dock",
        (0, -3900, 170),
        (0, 0, 90),
    )

    # Sunlight.
    sun = spawn_actor(
        unreal.DirectionalLight,
        "LIGHT_Sun_Directional",
        (0, 0, 5000),
        (-45, -35, 0),
    )
    sun_comp = sun.get_component_by_class(unreal.DirectionalLightComponent)
    if sun_comp:
        sun_comp.set_intensity(6.0)

    # Ambient sky fill.
    sky = spawn_actor(
        unreal.SkyLight,
        "LIGHT_SkyLight",
        (0, 0, 2500),
        (0, 0, 0),
    )
    sky_comp = sky.get_component_by_class(unreal.SkyLightComponent)
    if sky_comp:
        sky_comp.set_intensity(1.4)

    # UE sky atmosphere for visible sky color.
    spawn_actor(
        unreal.SkyAtmosphere,
        "ENV_SkyAtmosphere",
        (0, 0, 0),
        (0, 0, 0),
    )

    # Soft haze for the desert/ocean ruins mood.
    fog = spawn_actor(
        unreal.ExponentialHeightFog,
        "ENV_DesertSea_Fog",
        (0, 0, 80),
        (0, 0, 0),
    )
    fog_comp = fog.get_component_by_class(unreal.ExponentialHeightFogComponent)
    if fog_comp:
        fog_comp.set_fog_density(0.01)
        fog_comp.set_fog_height_falloff(0.25)

    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    unreal.log("LV_Extraction lighting and player start fixed.")


main()
