# Savannah Course: fallen log moved onto the path

Changed on 2026-10-08 for CatNapClub_Digiphant. The Savannah Course's **03 Fallen log** used to sit beside the path. It now lies across the path, so the elephant meets it on the route.

## What changed

| | Before | After |
| --- | --- | --- |
| Position on the route | 74 % of the way along (106.8 of 144.3 units) | 72 % of the way along (103.9 units) |
| Offset from the path's centre line | 4 units to the side (off the 4.2-unit-wide path) | 0, centred on the path |
| Position (course coordinates) | (15, 0, 12.56) | (19, 0, 9.67) |
| Rotation | Turned −25° around Y | 0°, lying across the path |

**Where it is now:** on the long straight stretch from (19, −12) to (19, 13), 3.3 units before the bend toward the finish. The route runs along +Z there. The log's 3-unit length lies along X, so it fits inside the path's 4.2-unit width.

**Why 72 % and not 74 %:** at 74 % the log would sit only 0.44 units before a bend, where the path turns a corner. Moving it back slightly puts it on a straight section.

## Files changed

1. **`Assets/StudentWork/Scenes/CatNapClub_DigiPhant.unity`**: the `03 Fallen log` transform under *Savannah Course [layout 4] → Landmarks (4, decorative)*.
2. **`Assets/SavannahCourse/Editor/SavannahCourseGenerator.cs`**, lines 320–323: the log is placed with `PointAlongRoute(.72f)` and no rotation, so **DigiPhant → Savannah → Regenerate Course in Open Scene** keeps the new position.

**Not changed:**
- `Prefabs/SavannahCourse.prefab` and the preview scene `Scenes/SavannahEnvironment.unity` still show the log beside the path.
- The other landmarks, trees, path, start and finish.

## Checking it in Unity

1. If Unity says the scene changed on disk, choose **Reload**. If you had unsaved changes in the scene, save them elsewhere first, or ask for the edit to be redone after you save.
2. In the Hierarchy, select *Savannah Course [layout 4] → Landmarks (4, decorative) → 03 Fallen log*, then press **F** in the Scene view. The log should lie across the sand-coloured path.
3. Optional: run **DigiPhant → Savannah → Validate Generator**. Its landmark check only requires landmarks within 30 units of the centre, and the log is 21.3 units away.

## Things to know

- **The log is decorative.** The course has no colliders and the elephant moves without physics, so it walks straight through the log. Stepping over it is up to the performers.
- **The Savannah Course files are not in Git yet.** `Assets/SavannahCourse/` was added on 2026-10-06 and is untracked, so the generator change is saved only on this computer until the group commits that folder.
- **Undo:** restore the scene transform to position (15, 0, 12.557159) and rotation (0, −0.21643962, 0, 0.976296). In the generator, put back `PointAlongRoute(.74f,-4)` and `Quaternion.Euler(0,-25,0)`.
