using System.Collections.Generic;
using System.Linq;
using DigiPhant;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace CatNapClub.Editor
{
    // Puts the CatNapClub cap on the elephant's Head bone, sized and placed from the head's own mesh,
    // so it follows the head through walking, turning and drinking. Running it again replaces the cap.
    public static class CatNapClubHat
    {
        const string Folder = "Assets/StudentWork/Hat";
        const string HatName = "CatNapClub Cap";
        // Crown base width in the generated OBJ files (StudentModels/make_cap.py).
        const float ModelWidth = 1f;
        // Cap width relative to the head, how far its band sits below the top of the head
        // (as a fraction of head width), and a slight backward tilt.
        const float WidthOfHead = .8f, Sink = .15f, TiltDegrees = -6f;

        [MenuItem("DigiPhant/Add CatNapClub Hat")]
        public static void Add()
        {
            if (EditorApplication.isPlaying) { Debug.LogWarning("Stop Play mode first, then add the hat."); return; }
            var c = Object.FindAnyObjectByType<DigiPhantController>();
            if (!c) { Debug.LogWarning("Open the CatNapClub_DigiPhant scene first."); return; }
            if (c.gameObject.scene.path == DigiPhant.Editor.DigiPhantSetup.ScenePath)
            { Debug.LogError("This is the starter's reference scene, which must stay unchanged. Open Assets/StudentWork/Scenes/CatNapClub_DigiPhant first."); return; }
            var movement = c.GetComponent<DigiPhantLocomotion>();
            var animator = movement && movement.elephantAnimator ? movement.elephantAnimator : Object.FindAnyObjectByType<Animator>();
            // Bones are named elephant_<Name>_bone; use the skinned mesh that the Head bone deforms.
            var skin = animator ? animator.GetComponentsInChildren<SkinnedMeshRenderer>()
                .Where(r => r.bones.Any(b => b && b.name == "elephant_Head_bone"))
                .OrderByDescending(r => r.sharedMesh ? r.sharedMesh.vertexCount : 0).FirstOrDefault() : null;
            if (!skin) { Debug.LogError("Could not find the elephant's Head bone (elephant_Head_bone)."); return; }
            var head = skin.bones.First(b => b && b.name == "elephant_Head_bone");
            var tail = skin.bones.FirstOrDefault(b => b && b.name == "elephant_Tail1_bone");
            var redMesh = LoadMesh("CapRed");
            var whiteMesh = LoadMesh("CapWhite");
            if (!redMesh || !whiteMesh) { Debug.LogError("Cap meshes missing in " + Folder + ". Let Unity finish importing, or run StudentModels/make_cap.py."); return; }

            // The head's surface: skinned vertices that mostly follow the Head bone, in world space.
            var baked = new Mesh();
            skin.BakeMesh(baked);
            var weights = skin.sharedMesh.boneWeights;
            int headIndex = System.Array.IndexOf(skin.bones, head);
            var points = new List<Vector3>();
            var vertices = baked.vertices;
            for (int i = 0; i < vertices.Length; i++)
                if (weights[i].boneIndex0 == headIndex && weights[i].weight0 >= .5f)
                    points.Add(skin.transform.TransformPoint(vertices[i]));
            Object.DestroyImmediate(baked);
            if (points.Count < 20) { Debug.LogError("Too few head vertices (" + points.Count + ") to fit the hat."); return; }

            var up = Vector3.up;
            var forward = tail ? Vector3.ProjectOnPlane(head.position - tail.position, up).normalized : animator.transform.forward;
            var right = Vector3.Cross(up, forward);
            float top = points.Max(p => p.y), bottom = points.Min(p => p.y);
            var crown = points.Where(p => p.y > top - (top - bottom) * .2f).ToList();
            var centre = crown.Aggregate(Vector3.zero, (sum, p) => sum + p) / crown.Count;
            float width = points.Max(p => Vector3.Dot(p, right)) - points.Min(p => Vector3.Dot(p, right));

            var materials = new[] { LoadMaterial("HatRed", new Color(.84f, .05f, .06f)), LoadMaterial("HatWhite", new Color(.95f, .95f, .95f)) };
            foreach (Transform child in head.Cast<Transform>().Where(t => t.name == HatName).ToList())
                Undo.DestroyObjectImmediate(child.gameObject);

            var hat = new GameObject(HatName);
            Undo.RegisterCreatedObjectUndo(hat, "Add CatNapClub hat");
            hat.transform.SetPositionAndRotation(new Vector3(centre.x, top - Sink * width, centre.z),
                Quaternion.LookRotation(forward, up) * Quaternion.Euler(TiltDegrees, 0, 0));
            hat.transform.localScale = Vector3.one * (WidthOfHead * width / ModelWidth);
            AddPart(hat, "Crown, brim and M", redMesh, materials[0]);
            AddPart(hat, "Badge", whiteMesh, materials[1]);
            Undo.SetTransformParent(hat.transform, head, "Attach hat to head");
            EditorSceneManager.MarkSceneDirty(c.gameObject.scene);
            Selection.activeGameObject = hat;
            Debug.Log("CatNapClub cap added to elephant_Head_bone (head width " + width.ToString("0.00") +
                      " units). Adjust it under elephant_Head_bone → " + HatName + " if needed, then save the scene.");
        }

        static void AddPart(GameObject hat, string name, Mesh mesh, Material material)
        {
            var part = new GameObject(name);
            part.transform.SetParent(hat.transform, false);
            part.AddComponent<MeshFilter>().sharedMesh = mesh;
            part.AddComponent<MeshRenderer>().sharedMaterial = material;
        }

        static Mesh LoadMesh(string file) =>
            AssetDatabase.LoadAllAssetsAtPath(Folder + "/" + file + ".obj").OfType<Mesh>().FirstOrDefault();

        static Material LoadMaterial(string name, Color colour)
        {
            string path = Folder + "/" + name + ".mat";
            var material = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (material) return material;
            material = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            material.SetColor("_BaseColor", colour);
            material.SetFloat("_Smoothness", .45f);
            AssetDatabase.CreateAsset(material, path);
            return material;
        }
    }
}
