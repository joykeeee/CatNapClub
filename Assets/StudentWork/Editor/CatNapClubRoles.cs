using System.Linq;
using DigiPhant;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace CatNapClub.Editor
{
    // Our three-person roles, applied to the open scene:
    // P1 front legs + travel, P2 steering by raising a hand, P3 trunk + ears.
    // Rear legs, tail sway and head turn are removed (the walk animation still moves the legs).
    // P3 holding up a bottle plays elephant@drink.
    public static class CatNapClubRoles
    {
        static readonly string[] Kept = { "Front left leg", "Front right leg", "Trunk curl", "Left ear", "Right ear" };

        [MenuItem("DigiPhant/Apply CatNapClub Roles")]
        public static void Apply()
        {
            if (EditorApplication.isPlaying) { Debug.LogWarning("Stop Play mode first, then apply the CatNapClub roles."); return; }
            var c = Object.FindAnyObjectByType<DigiPhantController>();
            if (!c) { Debug.LogWarning("Open the CatNapClub_DigiPhant scene first."); return; }
            if (c.gameObject.scene.path == DigiPhant.Editor.DigiPhantSetup.ScenePath)
            { Debug.LogError("This is the starter's reference scene, which must stay unchanged. Open Assets/StudentWork/Scenes/CatNapClub_DigiPhant first."); return; }
            var missing = Kept.Where(label => c.controls.All(x => x.label != label)).ToArray();
            if (missing.Length > 0) { Debug.LogError("Missing controls: " + string.Join(", ", missing)); return; }
            var movement = c.GetComponent<DigiPhantLocomotion>();
            if (!movement) { Debug.LogError("DigiPhant Controls has no DigiPhantLocomotion. Run DigiPhant → Add Locomotion To Open Scene first."); return; }

            Undo.RecordObjects(new Object[] { c, movement }, "Apply CatNapClub roles");
            // The three-person preset already puts front legs on P1 and trunk/ears on P3.
            c.SetPerformerCount(3);
            c.controls = c.controls.Where(x => Kept.Contains(x.label)).ToArray();
            movement.forward.sources = new[] { new MovementSource { performer = 1, movement = Movement.LeftHandHeight, weight = 1 } };
            // Average of (right hand - left hand): one hand up turns that way, both up goes straight.
            movement.steering.combination = SignalCombination.Average;
            movement.steering.sources = new[]
            {
                new MovementSource { performer = 2, movement = Movement.RightHandHeight, weight = 1 },
                new MovementSource { performer = 2, movement = Movement.LeftHandHeight, weight = -1 },
            };
            const string drinkPath = "Assets/Elephant/Animations/elephant@drink.fbx";
            movement.drink = AssetDatabase.LoadAllAssetsAtPath(drinkPath).OfType<AnimationClip>().FirstOrDefault(x => !x.name.StartsWith("__"));
            if (!movement.drink) Debug.LogWarning("Drink clip not found at " + drinkPath + "; the bottle trigger stays off.");
            movement.drinkPerformer = 3;
            EditorUtility.SetDirty(c);
            EditorUtility.SetDirty(movement);
            EditorSceneManager.MarkSceneDirty(c.gameObject.scene);
            Debug.Log("CatNapClub roles applied to " + c.gameObject.scene.name +
                      ": P1 front legs + forward/back (left hand), P2 steering (raise right hand = right, left hand = left), P3 trunk + ears, P3 bottle = drink. Save the scene to keep them.");
        }
    }
}
