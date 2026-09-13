"""Prompt templates and constants for the Virtual Lab AI assistant.

The classification instruction is defined exactly once and reused by both
chat branches (new user vs. returning user).
"""

CLASSIFICATION_INSTRUCTION = (
    "You are a highly knowledgeable and focused Virtual Lab AI lab assistant. "
    "Your sole purpose is to help users with science and engineering lab-related topics including: "
    "lab experiments and procedures, engineering theory relevant to labs, instrumentation and "
    "equipment usage, data analysis and scientific interpretation, safety protocols and best "
    "practices, and field-related technical questions. "
    "You must not answer any question that is NOT DIRECTLY related to science, engineering, or "
    "lab work. If a question is outside this scope (e.g., general knowledge, entertainment, "
    "personal advice), respond with exactly: "
    "\"I'm here to assist only with lab and engineering-related topics. Please ask a question "
    "related to science or laboratory work.\" "
    "Always keep your responses factual, concise, and focused on the topic. Use technical "
    "language suitable for students or professionals in STEM fields, but explain clearly when "
    "concepts may be complex."
)

CANONICAL_REFUSAL_TEXT = (
    "I'm here to assist only with lab and engineering-related topics. "
    "Please ask a question related to science or laboratory work."
)

GROUNDING_CONTEXT_TEMPLATE = """Use the following retrieved passages from lab-safety and
lab-procedure reference material as grounding context. Answer using this context when it is
relevant. If the retrieved context does not contain the answer, answer from the lab/engineering
knowledge you have, but do not contradict the context.

Retrieved passages:
{passages}
"""

EXTRACT_PHRASES_PROMPT = """Extract the {num_phrases} most important domain-specific phrases \
(1-4 words each) from the following experimental aim.
Return them as a JSON array of strings, no extra text.

Aim:
\"\"\"{aim_text}\"\"\"
"""

GENERATE_QUESTIONS_PROMPT = """I have these key phrases from an experiment:

{phrases_json}

For each phrase, write {num_questions} simple, one-sentence questions a student might ask to \
check their understanding of that phrase.
Return as a flat JSON array of strings, no extra text.
"""

GROUNDEDNESS_JUDGE_PROMPT = """You are evaluating whether an AI assistant's answer about lab practice is consistent with \
the retrieved reference context.

Answer: {answer}

Retrieved context:
{context}

Is the answer consistent with the context? Answer YES if the core guidance in the answer matches \
the context and does not contradict it (minor extra background details that do not conflict are \
acceptable). Answer NO if the answer contradicts the context, or if the answer's key claims about \
lab practice are neither supported by nor derivable from the context.

Reply with exactly one word: YES or NO.
"""
