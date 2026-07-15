import json
import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DISALLOWED_MODELS = {"Natori", "miku_sample_t04"}
DISALLOWED_RESOURCE_MODELS = DISALLOWED_MODELS | {"kei_basic_free", "miara_pro_t04"}
OLD_BACKGROUNDS = {
    "back_class_normal.png",
    "desk_foreground.png",
    "nokia_reception_desk.png",
    "nokia_reception_desk-backup.png",
}
LIVE2D_NOTICE = (
    "This content uses sample data owned and copyrighted by Live2D Inc."
)


class CompetitionAssetComplianceTest(unittest.TestCase):
    def test_disallowed_models_are_not_configured_or_importable(self):
        config = json.loads((PROJECT_ROOT / "config.json").read_text(encoding="utf-8"))
        configured = {
            item.get("model_name") for item in config["digital_humans"]["items"]
        }
        ignored = set(config["live2d"]["ignored_models"])

        self.assertTrue(DISALLOWED_MODELS.isdisjoint(configured))
        self.assertTrue(DISALLOWED_MODELS.issubset(ignored))

    def test_readme_contains_live2d_and_third_party_notices(self):
        readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")

        self.assertIn(LIVE2D_NOTICE, readme)
        self.assertIn("THIRD_PARTY_NOTICES.md", readme)
        self.assertTrue((PROJECT_ROOT / "THIRD_PARTY_NOTICES.md").is_file())

    def test_local_competition_assets_exclude_disallowed_files(self):
        library = PROJECT_ROOT / "library"
        resources = library / "live2d" / "Samples" / "Resources"
        if not resources.is_dir():
            self.skipTest("Local Live2D resources are not installed")

        model_dirs = {path.name for path in resources.iterdir() if path.is_dir()}
        audio_files = [
            path for path in resources.rglob("*") if path.suffix.lower() in {".wav", ".mp3", ".ogg", ".m4a"}
        ]
        old_backgrounds = [path for path in resources.rglob("*") if path.name in OLD_BACKGROUNDS]
        zip_files = list(library.rglob("*.zip"))

        self.assertTrue(DISALLOWED_RESOURCE_MODELS.isdisjoint(model_dirs))
        self.assertEqual([], audio_files)
        self.assertEqual([], old_backgrounds)
        self.assertEqual([], zip_files)


if __name__ == "__main__":
    unittest.main()
