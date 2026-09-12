# ZHJ Testing Expert

This is the tracked source for the WorkBuddy expert maintained by the ZHJ Testing Team. Its primary business line is ZHJ plus Operations. ZHJ Retail, AI Inventory, and International Ailit are available only to employees authorized by the MySQL roster.

Run `python tools/build_workbuddy_package.py` to create the local WorkBuddy archive. The builder copies the current `ZHJ_test_skills/` suite into the package and validates the manifest, avatar, agent, prompt mapping, and skill entry. Generated files in `deliverables/` are intentionally ignored by Git.
