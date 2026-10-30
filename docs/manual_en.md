# PrismShotFrame Manual

PrismShotFrame is free. There is no license key, no watermark, and no export resolution cap.

Looking Glass Portrait / Go can display the exported quilts (Looking Glass is a trademark of Looking Glass Factory).

## Requirements

- Windows
- Python 3.11 for Studio
- Unity 2022.3.22f1 for Shot and Frame
- VRChat Creator Companion
- Modular Avatar 1.9 or newer for avatars
- UdonSharp for worlds

## Studio

Do not create a virtual environment. From the `studio` folder:

```powershell
py -3.11 -m pip install -e ".[dev]"
$env:PYTHONDONTWRITEBYTECODE = "1"
py -3.11 -m pytest
py -3.11 scripts/download_model.py
py -3.11 -m prismshot
```

Install `onnxruntime-directml` only. Do not also install `onnxruntime`.

The window lists pictures from the VRChat folder and accepts drag and drop. Pictures without the RGB-D mark are given depth by Depth Anything V2 Small. If the model file is missing, Studio reports that and keeps running.

You can change disparity, focus, columns, rows, hole fill (simple or high), and edge refinement. Move the mouse across the preview to change the view. Export a quilt, a side-by-side pair, or an RGB-D image. Multi-select the list to convert a batch.

Quilt files are named `original_qs{columns}x{rows}a{aspect}.png`. The default grid is 8x6 for portrait and 11x6 for landscape.

## Shot

1. Open an avatar project in Unity 2022.3.22f1 with the Avatars SDK and Modular Avatar.
2. Add `unity/PrismShotFrame.Shot/Packages/com.prismshotframe.shot` as a local package.
3. Run `PrismShot/Build Shot Prefab`.
4. Put `Assets/PrismShotFrame/Generated/PrismShot.prefab` under a hand.
5. Upload. The Android build removes this object.

The cameras stay off until the menu item "出す" is enabled. Frame the back card so it fills the VRChat photo. The left half is color and the right half is depth.

## OSC

Enable OSC in VRChat. Studio reads the OSCQuery port from the VRChat log. It can toggle the camera, distances, zoom, the depth preview, and the shutter. Studio does not exit when VRChat is closed.

See [osc_parameters.md](osc_parameters.md). New RGB-D pictures in the photo folder are opened in the preview.

## Frame

1. Open a world project with the Worlds SDK and UdonSharp.
2. Add `unity/PrismShotFrame.Frame/Packages/com.prismshotframe.frame`.
3. Run `PrismShot/Build Frame Prefabs`.
4. Place a prefab and assign a picture on the Picture material.
5. Select Picture and run `PrismShot/Read Picture Name On Selection`.

A name containing `qs8x6` switches to the quilt shader. Otherwise the material stays RGB-D. Use RGB-D on Quest.

There are flat, bordered, and thick frames. The slideshow advances locally on each client, so every slide should use the same layout.

`PrismShot/Create Sample Scene` replaces the open scene. Save first.

## When something looks wrong

- Treated as a normal photo: the card did not fill the frame. Use AI depth, or shoot again with the card filling the photo.
- Depth looks wrong: turn on AI depth. Avatar-camera depth is not yet verified in VRChat.
- The card is invisible: the main camera may not draw layer 4.
- Compile errors: match the asmdef references to the assembly names in your project.

The check procedure is in [DEBUG_CHECKLIST.md](DEBUG_CHECKLIST.md).
