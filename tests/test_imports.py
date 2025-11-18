def test_imports():
    # Ensure modules import correctly (basic smoke test)
    import diligent_ai
    from diligent_ai import config, pdf_utils, llm_client, verifier, agent

    # Basic checks
    assert hasattr(config, "load_config")
    assert hasattr(pdf_utils, "extract_text_from_pdf")
    assert hasattr(llm_client, "LLMClient")
    assert hasattr(verifier, "extract_claims_from_text")
    assert hasattr(agent, "generate_questions")
