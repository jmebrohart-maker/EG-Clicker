# waytool 1.0.1 provenance

These public Sigstore bundles were retrieved from GitHub's artifact-attestation
API for the two Fedora 44 RPMs. They contain public certificates and signatures,
not credentials. Original publisher: https://github.com/mx-shift/waytool

Approved SHA-256 digests:

- x86_64: `d8158b07c2f7aa18f1592668e07c189ffb9e20f78b648519a93a58c26e29658b`
- aarch64: `e1b97b70e10cb6c9d01865f16a7299a598c84e117fd6adcbcf3f18d9f70324e9`

The installer checks the exact pinned bytes and uses Fedora's `gh` package to
verify the bundle against Sigstore's trust roots, enforcing:

- Repository: `mx-shift/waytool`
- Certificate identity: `https://github.com/mx-shift/waytool/.github/workflows/ci.yml@refs/tags/v1.0.1`
- Source digest: `007baab54cc9142d27c353790976cefcf62224e6`
- GitHub-hosted runner (self-hosted runners rejected)

A bundled attestation avoids requiring GitHub login. Verification still needs
HTTPS access to refresh Sigstore trust metadata. Any checksum, signature, trust,
or tooling error stops installation of the downloaded RPM.

Both original RPMs verified successfully with these policies. Changing one byte
of the x86_64 RPM caused verification to fail. These attestations establish
build origin and integrity; they are not an audit of the third-party program.

When changing waytool versions, obtain the new artifacts and attestations,
review the source/workflow change, verify provenance for both architectures,
and update the pinned hashes, source digest, certificate identity, and bundles
together. Never replace a failed verification with an unsigned fallback.
