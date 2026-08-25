# R13.4 candidate note

This note freezes the first CI candidate only. It does not constitute PASS evidence.

Candidate scope: governed Android Gradle build/export with source-manifest verification, isolated staging overlay, fixed Gradle tasks, hosted Ubuntu/Windows toolchain evidence, APK/AAB structural inspection and exact-head JSON evidence.

The candidate must pass R0, full Python Core, KodeStudio UI Smoke and the dedicated R13 Android Build Acceptance workflow on the same head. Any failure rejects the candidate. Manual gate remains CONDITIONAL and is not triggered before hosted CI is exhausted.
