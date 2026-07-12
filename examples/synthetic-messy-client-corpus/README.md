# Synthetic messy client corpus

This fixture is fictional. It models the pre-ingest problem a client corpus creates before the Biotech RAG Assistant can trust retrieval: document identity, version, status, and effective date may live in filenames, source registers, or document headers.

The onboarding command maps this bundle into the clean `metadata/` plus `documents/` shape consumed by `validate-corpus`. Documents that need review or are rejected do not get clean sidecars. Retrieval nominates candidate passages from the normalized corpus; it does not certify truth or compliance.
