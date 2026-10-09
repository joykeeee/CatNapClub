# DigiPhant setup — CatNapClub_Digiphant

Setup record for integrating the DigiPhant elephant, motion tracking and recording
into this Unity project. Last updated 2026-10-08. Each check below says whether it
was **verified** or is **still to do**; nothing listed as pending has been tested.

## 1. Actual environment

| Item | Value |
| --- | --- |
| Computer | Intel Mac, Core i5-8257U (x86_64, not Apple Silicon) |
| OS | macOS 15.8.1 (24H32) |
| Unity editor | 6000.6.3f1 (x86_64), `/Applications/Unity/Hub/Editor/6000.6.3f1` |
| Render pipeline | URP 17.6.0 (`Assets/Settings/PC_RPAsset.asset`, `Mobile_RPAsset.asset`) |
| Input handling | Input System package only (`activeInputHandler: 1`), left unchanged |
| Python | 3.11.4 (python.org build, `/Library/Frameworks/Python.framework/Versions/3.11`) |
| Tracking deps | mediapipe 0.10.21, opencv-contrib-python 4.11.0.86, numpy 1.26.4 |
| Cameras | index 0 = built-in FaceTime HD (1280×720); index 1 = iPhone Continuity Camera (1920×1080) |

### Why the Python pins differ from the starter

The starter pins `mediapipe==0.10.35` and `opencv-contrib-python==4.14.0.94`
(reference: Apple Silicon, Python 3.14). MediaPipe 0.10.35 publishes **no macOS
x86_64 wheel**, so it cannot be installed on this Intel Mac. MediaPipe 0.10.21 is the
newest release with an Intel macOS wheel (Python 3.9–3.12). It requires `numpy<2`,
which conflicts with OpenCV 4.14, so pip resolved OpenCV 4.11.0.86.

The pins are recorded in [StudentTracking/requirements-macos-intel.txt](StudentTracking/requirements-macos-intel.txt)
(tracked in this repository). The starter's own `requirements.txt` is unchanged.
`bridge.py` and `encode_recording.py` run unmodified on these versions. The
PoseLandmarker Tasks API is available, and landmarks expose both `visibility` and
`presence`.

## 2. Locations

| What | Path |
| --- | --- |
| Starter repository | https://github.com/kommanderpi/studentstarter.git |
| Starter commit used | `5adcbea1f7b311b8bb15c17b3dc4742ae8fff3af` (main) |
| Starter clone | `DigiPhantStarter/` beside `Assets/` (ignored by this repo) |
| Elephant assets | `Assets/Elephant/` + `Assets/Elephant.meta` (unchanged copy, ignored by Git) |
| DigiPhant scripts/scene | `Assets/DigiPhant/` + `Assets/DigiPhant.meta` (tracked copy; validator fix and side-by-side preview, section 7) |
| Our scene | `Assets/StudentWork/Scenes/CatNapClub_DigiPhant.unity` (copy of the reference scene) |
| Python environment | `DigiPhantStarter/Tracking/.venv` (Python 3.11.4) |
| Bridge / encoder / model | `DigiPhantStarter/Tracking/bridge.py`, `encode_recording.py`, `pose_landmarker_full.task` |
| Bottle model | `DigiPhantStarter/Tracking/efficientdet_lite0.tflite` (MediaPipe EfficientDet-Lite0 int8, 4,602,795 bytes, SHA-256 `0720bf24…c723bb`; not in the starter, download in section 9) |
| Recordings | `Recordings/<date-time-id>/performance.mp4` (ignored; final video goes on Drive) |

The camera launcher (`DigiPhantCameraPreview.cs`) and recorder (`DigiPhantRecording.cs`)
both resolve `Application.dataPath + "/../DigiPhantStarter/Tracking"` and
`.venv/bin/python`. This matches the layout above, so neither script was changed.

## 3. How tracking data reaches the elephant

```text
Webcam (index 0)
  └─ bridge.py  (Python, launched by Unity on Play, --no-window)
       MediaPipe PoseLandmarker → up to 4 skeletons per frame
       --zones (our default): frame split into N vertical strips, P1 leftmost; MediaPipe runs
         on each strip separately and the body centred nearest its middle drives that slot
       otherwise: PerformerTracker → slots P1..Pn, assigned left-to-right, then followed by position
       extract_features → 6 body-relative signals + confidence per performer
       --bottle: EfficientDet-Lite0 every 0.4 s, class "bottle" only; a bottle belongs to the
         performer whose visible wrist or finger point is on or next to it (kept for 1 s to ride
         over missed detections) → "bottle": true in that person's data; boxes are labelled
         "PN bottle" (counted) or "bottle (no hand)" (ignored)
       ├─ UDP 127.0.0.1:5055  JSON snapshot  ─────────────▶ DigiPhantController (Unity)
       └─ UDP 127.0.0.1:5057  annotated JPEG preview ─────▶ DigiPhantCameraPreview (Unity)
  ◀─ UDP 5055→5056  {"performerCount", "upperBodyOnly", "reset"} every 0.5 s from Unity

DigiPhantController (each LateUpdate)
  validate packet → store values/confidence per slot, timestamp arrival
  neutral calibration (10 s countdown) saves each performer's resting values
  per control: (current − neutral) × sensitivity → clamp ±1 → smoothing
  → rotate each mapped bone from its rest pose about a local axis by ±degrees
DigiPhantLocomotion: P1 left-hand height → forward/back speed, P1 lean → steering,
  blends the supplied walk/run/turn clips; gestures are layered on top.
DigiPhantRecording: captures the Game view (preview + elephant) at 10 fps → JPEGs
  → encode_recording.py → performance.mp4
```

The six signals are `LeftHandHeight, RightHandHeight, LeftFootLift, RightFootLift,
Lean, ArmSpread`. They are image-space ratios normalised by torso length, or by
shoulder width when seated. They are not angles or metres. Unity drops tracking
older than 0.5 s and ignores inputs whose confidence is below 0.5. All traffic stays
on this computer.

## 4. Scene, launch, group size and mappings

- **Open:** `Assets/StudentWork/Scenes/CatNapClub_DigiPhant.unity`. The reference
  `Assets/DigiPhant/Scenes/DigiPhant.unity` is kept untouched for comparison.
- **Launch:** press Play. Unity starts the bridge automatically after about one
  second and shows the preview. Stopping Play kills the bridge Unity started. To
  run the bridge by hand instead (with its own preview window):
  `DigiPhantStarter/Tracking/.venv/bin/python DigiPhantStarter/Tracking/bridge.py --people 1 --upper-body-only`
  (Q to quit, R to reassign). Quit it before pressing Play, since only one bridge
  can own ports 5055–5057.
- **Camera index:** 0 (built-in). If the iPhone is nearby and Continuity Camera
  takes over, set `cameraIndex` on the *DigiPhant Controls* object's
  DigiPhantCameraPreview component, or pass `--camera 1`, after checking which
  device appears.
- **Group size:** our group has three people. The scene is the reference default
  (3 performers, Full body). Solo testing uses 1 + *Seated / upper body*.
- **Mappings:** CatNapClub roles (2026-10-06), applied with **DigiPhant → Apply CatNapClub Roles**
  ([Assets/StudentWork/Editor/CatNapClubRoles.cs](Assets/StudentWork/Editor/CatNapClubRoles.cs)).
  Run it with the scene open and Play stopped, then save the scene. Rear legs, tail sway
  and head turn are removed on purpose (the walk animation still moves the legs).
  Changing group size in Play re-applies the starter presets to the remaining controls
  and can move steering to P1; run the menu again afterwards.

| Performer | Input (full body / seated) | Elephant |
| --- | --- | --- |
| P1 | foot lifts / hand raises | front legs |
| P1 | left-hand height | travel forward/back (walk → run) |
| P2 | raise right hand / raise left hand (average of right − left height) | turn right / turn left; both up = straight |
| P3 | right-hand height | trunk curl |
| P3 | hand separation | ears |
| P3 (last performer in smaller groups) | holds up a bottle for 0.6 s | plays `elephant@drink` once (about 6.7 s), standing still; lower the bottle before the next drink |

Seated: P1's left-hand raise drives both the front left leg and forward travel, as in the
starter. Calibration now needs only these inputs visible, so P2's and P3's feet do not
need to be in frame.

## 5. Calibrate, stop, restart and recover

1. In Play: choose the group size, then *Full body* or *Seated / upper body*, then *Camera*.
2. **Zones (default, *One person per zone* ticked):** the preview shows white lines and
   a *PN zone* label per strip, P1 leftmost in the unmirrored image (the performer
   furthest to the right as seen by the group facing the camera). Each person stands
   (full body) or sits (seated) centred in their own strip; *PN zone: step in* means
   nobody is centred there. Full body: hips decide the zone, and head to feet must fit
   in the frame. Seated: shoulders decide the zone; shoulders and hands must be visible.
   A body is grey if it is the second person in a strip. Each zone works on its own,
   so nobody waits for the rest of the group. Wait until every *Performer N · visible*
   shows. Without zones, assignment waits for the full group, ordered left-to-right.
3. Click **Set neutral pose (10 seconds)**, get into a resting pose with every
   mapped body part visible, and hold still. If it fails ("needs all assigned
   movements visible"), fix the framing and repeat. P1's left hand should rest
   around waist height so it can go up (forward) and down (backward).
4. **Tracking lost:** affected controls ease back to rest and travel stops. They
   resume when tracking returns, and the existing calibration remains valid.
5. **Wrong person controls a part** (after crossing or occlusion): with zones, move
   back into your own strip; without zones, click **Reassign people**. Then set the
   neutral pose again.
6. **Camera stopped / no preview:** click **Retry**. Close other apps using the
   camera and any manually started bridge. Check camera permission (section 7).
7. Changing group size, movement mode or *One person per zone* clears calibration, so
   recalibrate afterwards. Toggling zones restarts the camera bridge (a second or two).
   **Return to starting position** also clears it.

## 6. Recording (RECORDING.md)

Already integrated. `DigiPhantController` adds `DigiPhantRecording` automatically
in Play mode, and the recorder uses the same venv to run `encode_recording.py`.
No changes were needed.

1. Calibrate in Camera mode, keep the **Game** view visible (≥1280×720 if
   possible), then click **Record performance**.
2. Click **Stop recording and save** and wait for *Saved: …/performance.mp4*.
3. Check the MP4 in `Recordings/<session>/` (beginning, end, one action per performer).
4. Upload it manually to the team Drive folder (e.g. `CatNapClub_P2/Recordings/`),
   check that it plays and is shared, and put the link in `README.md`. Nothing
   uploads automatically. MP4s and frame folders are ignored by Git.
5. Retry an export:
   `DigiPhantStarter/Tracking/.venv/bin/python DigiPhantStarter/Tracking/encode_recording.py --session "Recordings/SESSION_FOLDER"`.
   The output uses the `mp4v` codec. If a player rejects it, transcode a copy to
   H.264 (ffmpeg is not installed here; `brew install ffmpeg` would add it).

## 7. Changes made

| Change | Reason |
| --- | --- |
| Copied `Elephant/`, `Elephant.meta`, `DigiPhant/`, `DigiPhant.meta` into `Assets/` | Fresh import; destinations did not exist; metadata preserved |
| Created `DigiPhantStarter/Tracking/.venv` with Python 3.11.4 | Only interpreter present that has MediaPipe Intel-Mac wheels |
| Added `StudentTracking/requirements-macos-intel.txt` | Documented, tested replacement pins (section 1) |
| Added `Assets/StudentWork/Scenes/CatNapClub_DigiPhant.unity` | Working copy so the reference scene stays recoverable |
| Added `.gitignore`, initialised Git (`main`), staged files | STUDENT_GIT.md lightweight repository |
| Added `DIGIPHANT_SETUP.md`, `README.md` | This record and the submission index |
| Added `Assets/StudentWork/Editor/CatNapClubRoles.cs` (menu *DigiPhant → Apply CatNapClub Roles*) (2026-10-06; run it once on our scene and save) | Group roles (section 4); our own file, no starter code changed |
| Savannah fallen log moved onto the path (2026-10-08): scene transform and `SavannahCourseGenerator.cs` | Group request; details, before/after and undo in [SAVANNAH_LOG_CHANGE.md](SAVANNAH_LOG_CHANGE.md) |
| Cap for the elephant (2026-10-08): [StudentModels/make_cap.py](StudentModels/make_cap.py) generates `Assets/StudentWork/Hat/CapRed.obj` (crown, brim, embossed M) and `CapWhite.obj` (badge) from the group's reference images; [Assets/StudentWork/Editor/CatNapClubHat.cs](Assets/StudentWork/Editor/CatNapClubHat.cs) adds *DigiPhant → Add CatNapClub Hat*, which measures the head from the skinned vertices weighted to `elephant_Head_bone`, sizes the cap to 80 % of head width, faces it forward (head minus `elephant_Tail1_bone`), tilts it back 6°, parents it to the head bone and creates `HatRed.mat` / `HatWhite.mat` (URP Lit). Running it again replaces the cap; it refuses the reference scene | Group request. Parented to the bone, so it follows walking, turning and drinking. Shape checked in matplotlib previews only; placement not yet seen in Unity. Regenerate the OBJ files with `DigiPhantStarter/Tracking/.venv/bin/python StudentModels/make_cap.py [--preview DIR]` |
| Bottle → drink (2026-10-08): `bridge.py` gains `--bottle` / `--object-model` and `bottle_holders`, sends `bottle` per person and draws yellow bottle boxes; new `test_bottle.py` (4 tests). `DigiPhantController.cs` stores the flag (`IsHoldingBottle`) and pauses pose controls while drinking; `DigiPhantLocomotion.cs` gains `drink`, `drinkPerformer`, `drinkHoldSeconds`, the drink action and a *Test drink* button (Test sliders); `DigiPhantCameraPreview.cs` gains `detectBottle` (default on, passes `--bottle` only if the model file exists). `CatNapClubRoles` assigns `elephant@drink` and P3, and now refuses to run on the reference scene. Patch: [StudentTracking/bottle-drink.patch](StudentTracking/bottle-drink.patch) (apply after `zones.patch`) | Group request: P3 shows a water bottle → elephant drinks. Wrist-on-bottle rule ignores bottles on tables or in other hands. Checked: 20/20 Python tests; headless 10 s run with `--zones --bottle` sends the new field with no errors; steady rate on an empty scene 4.8 packets/s (zones) vs 5.7 (zones + bottle), so the 0.4 s check costs no measurable rate. First live test (2026-10-08): box appeared but no drink. Follow-up: hand points 17–22 count as well as wrists, holder kept 1 s, box labels show the owner, smaller groups use the last performer, and the panel says why it is not drinking (*P3 not tracked* / *no bottle in P3's hand* / *lower the bottle…*). 21/21 Python tests; 10 s headless run clean |
| Patched `Assets/DigiPhant/Editor/DigiPhantSetup.cs`: `c.inputMode = InputMode.Camera;` after `Three();` in `Validate()` (2026-10-06). Patch: [StudentTracking/validate-seated-camera-mode.patch](StudentTracking/validate-seated-camera-mode.patch) | Starter bug: the UDP checks leave the controller in Test sliders mode, so the seated checks always failed with "Seated hand input failed to drive leg" (and the countdown checks would fail next). Validation test only; runtime behaviour unchanged. Not fixed upstream as of `4e6dab5` |
| Side-by-side camera preview (2026-10-06): `DigiPhantController.cs` gains `sideBySidePreview` (default on) and splits the area right of the controls 50/50, camera preview left, elephant right; `DigiPhantCameraPreview.cs` gains `DrawStage` and can skip the panel thumbnail. Patch: [StudentTracking/side-by-side-preview.patch](StudentTracking/side-by-side-preview.patch) | Group request: preview as large as the game view. Turn off with *DigiPhant Controls → DigiPhant Controller → Side By Side Preview*. The bridge still sends at most 320×240 (one UDP datagram), so the large preview is upscaled and soft. Recordings capture the split view |
| Zone detection (2026-10-06): `bridge.py` gains `--zones` (`zone_bounds`, `to_frame`, `zone_choice`) and draws the zone lines; new `test_zones.py` (5 tests); `DigiPhantCameraPreview.cs` gains `useZones` (default on) and passes `--zones`; the controls panel gains *One person per zone (P1 left)*. Changing group size in Test sliders mode restarts the bridge so its zones follow (the starter only sends the count in Camera mode). Patch: [StudentTracking/zones.patch](StudentTracking/zones.patch) (apply after the two patches above) | Three people were not all detected at once in one full-frame pass. Each strip is detected separately (crops widened by 6 % of frame width for reaching arms; body centre must be inside the strip), so each person is larger in the detector's input, and zone = identity, so no full-group wait or crossing swaps. Works in full body and seated: unchanged `extract_features` on landmarks mapped back to the whole frame gives the same values as before. Cost: one detector per zone, lower frame rate (section 10) |

No project settings, packages, render pipeline, input settings or existing assets
were changed. `SampleScene` is untouched. The code changes are those listed above, so `DigiPhantSetup.cs`,
`DigiPhantController.cs`, `DigiPhantCameraPreview.cs` and `DigiPhantStarter/Tracking/bridge.py`
no longer match their starter checksums. `DigiPhantStarter/` is not in this repository, so the
bridge change lives only in `StudentTracking/zones.patch` (section 9).

## 8. Verification results

### Static and automated (verified 2026-10-05)

- Asset import provenance: 247/247 SHA-256 comparisons match `asset-checksums.json`
  (starter sources, `Assets/` copies, and the pose model).
- `pip check`: no broken requirements. Imports print MediaPipe 0.10.21 / OpenCV 4.11.0.
- Python tests: 21/21 pass on 2026-10-08 (11 supplied + 5 in `test_zones.py` + 5 in `test_bottle.py`). Originally 11/11 (feature extraction, performer matching,
  preview JPEG size, MP4 encoder duration/gap handling, error reporting).
- Pose model loads in MediaPipe 0.10.21 (VIDEO mode, 4 poses).
- Git: 102 files (~816 KB) staged; no FBX, textures, pose model, venv, Library or recordings.
- Fresh-checkout reconstruction (scratch copy of the staged files + starter cloned at
  `5adcbea` + `Elephant` restored): 91 asset metas and 274 referenced GUIDs, with an
  unresolved set identical to the working project (only package/built-in references).

### Live (verified from Terminal, outside Unity)

- Camera index probe: index 0 opens at 1280×720, and one person was detected in a single frame.
- Bridge end-to-end, headless, 1 person seated, 8 s run: 61 tracking packets received
  on 127.0.0.1:5055 (about 15/s on this CPU), P1 assigned in 57, 31 preview JPEGs on 5057.
  The bridge applied a Unity-style configuration command sent from port 5055 to 5056.
  Hand confidences were 0 because the hands were out of frame, so framing matters.

### Unity editor (observed 2026-10-05, from Logs/Editor.log and running processes)

- Project opened from Unity Hub in 6000.6.3f1 (x86_64). The import finished with no
  C# compiler errors, and Unity generated the `Assets/StudentWork` metas.
- `CatNapClub_DigiPhant` opened, and the elephant is visible (reported by the user).
- Play: Unity auto-launched the bridge (`--no-window --people 3 --camera 0`). On the
  first launch macOS had not yet authorised the camera ("not authorized to capture
  video … requesting"). After that, a Unity-launched bridge was running and Unity's
  preview socket (5057) was open. On a new machine, expect to allow camera access
  once and then click **Retry**.
- Note: the project has Enter Play Mode Options enabled (no domain/scene reload),
  which is the URP template default. The DigiPhant scripts reset their state in OnEnable.

### Not yet verified (needs the Unity editor and people)

- [x] `DigiPhant → Validate Saved Template` (reference scene) in the editor. **Passed
      2026-10-06** (`DIGIPHANT_VALIDATION_OK`) after the fix and scene restore below. First run
      (2026-10-06, unpatched) passed rig, sliders, reset, packets, timeout, UDP and presets,
      then failed at the seated checks because of the starter bug fixed in section 7.
      Second run failed with "Baseline rejected": the save prompt had written the
      failed run's leftover test state into the reference scene (seated mode, port 54312,
      locomotion off). The scene was restored from Git (matches the starter); the rerun passed.
- [ ] Play: preview image visible in the Game view; Test sliders move legs/head/trunk/ears/tail.
- [ ] Camera mode: solo calibration plus one elephant response (e.g. raise a hand → front leg).
- [ ] Tracking loss and recovery (step out of frame, then return).
- [ ] Recording: short take, MP4 exported, plays with camera panel and elephant visible.
- [ ] Three-person assignment, calibration and each role, with zones in full body and
      seated (zone mode is unit-tested and smoke-tested in MediaPipe, but not yet live).
- [ ] Git: `Assets/StudentWork*.meta` generated and staged (107 files); first
      commit, remote and push still to do.
- [ ] Drive upload and link in README.

## 9. Restore from a fresh checkout of this repository

```sh
cd CatNapClub_Digiphant
git clone https://github.com/kommanderpi/studentstarter.git DigiPhantStarter
git -C DigiPhantStarter checkout 5adcbea1f7b311b8bb15c17b3dc4742ae8fff3af
cp -R DigiPhantStarter/Elephant Assets/Elephant
cp DigiPhantStarter/Elephant.meta Assets/Elephant.meta
# Do NOT copy DigiPhantStarter/DigiPhant over Assets/DigiPhant: our tracked copy wins.
# Intel Mac (this machine): Python 3.9-3.12 with the Intel pins
python3.11 -m venv DigiPhantStarter/Tracking/.venv
DigiPhantStarter/Tracking/.venv/bin/python -m pip install -r StudentTracking/requirements-macos-intel.txt
# Apple Silicon / Windows: use DigiPhantStarter/Tracking/requirements.txt (starter pins) instead
DigiPhantStarter/Tracking/.venv/bin/python -m pip check
curl -L -o DigiPhantStarter/Tracking/efficientdet_lite0.tflite https://storage.googleapis.com/mediapipe-models/object_detector/efficientdet_lite0/int8/latest/efficientdet_lite0.tflite
shasum -a 256 DigiPhantStarter/Tracking/efficientdet_lite0.tflite  # 0720bf247bd76e6594ea28fa9c6f7c5242be774818997dbbeffc4da460c723bb
DigiPhantStarter/Tracking/.venv/bin/python -m unittest discover -s DigiPhantStarter/Tracking -p 'test_*.py'
```

The pose model `DigiPhantStarter/Tracking/pose_landmarker_full.task` comes with the
starter clone. Then open the project in Unity 6000.6.3f1 and open
`Assets/StudentWork/Scenes/CatNapClub_DigiPhant.unity`. No shared assets or tracking
code are modified apart from the patches in `StudentTracking/`. The C# side of all three is
already in the tracked `Assets/DigiPhant` copy. **The bridge is not**: after cloning the
starter, apply the bridge part of the zone patch, or zone mode will fail to start
(`bridge.py: error: unrecognized arguments: --zones`):

```sh
git -C DigiPhantStarter apply --include='Tracking/*' ../StudentTracking/zones.patch
git -C DigiPhantStarter apply --include='Tracking/*' ../StudentTracking/bottle-drink.patch
```

To rebuild the starter's own `DigiPhant/` copy as well, apply all three in order:
`validate-seated-camera-mode.patch`, `side-by-side-preview.patch`, `zones.patch`,
`bottle-drink.patch` (checked 2026-10-08: the result matches the project files byte for byte).
If anyone edits `bridge.py` again, regenerate the patch and note it here.

## 10. Limitations and notes

- **Python version lock:** this Intel Mac must stay on MediaPipe ≤0.10.21 and
  Python ≤3.12. Do not upgrade to the starter pins here.
- **Frame rate:** about 15 tracking frames/s on the i5-8257U with the full model.
  Expect more lag than the reference machine, and more again with three people.
  Zone mode runs one detector per zone: measured on blank frames, 11.5 frames/s for 3
  zones and 9.2 for 4 (38.6 for 1), before any people are tracked. With people in view,
  expect roughly 5–8 frames/s for three. Measured 2026-10-08 on an empty scene, Unity closed:
  4.8 packets/s for 3 zones (5.7 with bottle detection), so expect visible lag. If it is too slow, untick
  *One person per zone*.
- **Vendor demo scene:** `Assets/Elephant/Scenes/SampleScene.unity` uses the vendor
  `Elephant.cs`, which reads the old Input Manager. With Input System only, its
  keyboard controls throw errors there. The DigiPhant scenes disable that component
  and are unaffected. The global input setting was not changed.
- **Batch Unity from the agent:** two Unity processes started from the agent's
  terminal (`-version`, `-batchmode`) hung in an unkillable exiting state (`UE`)
  before writing any log or lock file. If Unity Hub reports the project already
  open, restart the Mac.
- Automatic bridge launch and recording are Editor-only. A built player needs a
  manually started bridge.
- **Reference scene restored again (2026-10-08):** on 2026-10-06 18:16 it was saved with the
  CatNapClub roles applied (the menu was run while it was open). Restored from Git;
  `CatNapClubRoles` now refuses to run on it.
- **Bottle detection:** COCO "bottle" class at score ≥ 0.35. Clear or small bottles, or a
  bottle mostly hidden by the hand, may be missed; hold it up sideways, near the face, in
  good light. In Test sliders mode the trigger is off; use *Test drink* to preview the clip.
- **Validator save prompt:** if `Validate Saved Template` fails partway, the open
  reference scene keeps its test settings in memory. When Unity next asks to save it,
  choose **Don't Save**, or the reference scene gets seated mode, a temporary port and
  locomotion off. Restore with `git checkout -- Assets/DigiPhant/Scenes/DigiPhant.unity`.
- Performer identity follows position, not appearance. With zones, identity is the
  strip a person is centred in; without zones, use Reassign after crossings.
- **Zone framing:** with 3 zones at 1280×720 each strip is about 430 px wide, so full-body
  performers must stand far enough back to fit head to feet. Two people centred in one
  strip: only the one nearest the middle counts.
