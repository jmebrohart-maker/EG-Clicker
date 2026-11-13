# Release checklist

1. Update the Python and Cargo versions together, plus README and changelog.
2. Run Python GUI tests, Rust tests, ShellCheck and the manifest check. Record any
   live desktop validation separately; automated tests simulate desktop integration.
3. Merge the reviewed release commit into `main` and wait for CI to pass.
4. Create an annotated `vX.Y.Z` tag on that exact commit. Do not move existing tags.
5. From a clean checkout of the tag, build the source/install bundles:

   ```bash
   python3 scripts/build_release.py --version X.Y.Z --output-dir dist
   ```

6. Verify the tar.gz/ZIP contents and `SHA256SUMS`. The build is reproducible for
   the same tracked bytes, file modes, commit timestamp and packaging toolchain. Packages contain the
   Python app, installer, Rust source, documentation and provenance bundles;
   they do not contain a standalone compiled GUI executable.
7. Create a draft GitHub release, upload both bundles and `SHA256SUMS`, and write
   notes describing behavior, compatibility and known limitations.
8. Check the install URL and publish the release as latest. Verify the public
   downloads after publishing.

Keep the previous releases and tags available for existing links. Signatures
must only be claimed when a verifiable signing process actually produced them.
