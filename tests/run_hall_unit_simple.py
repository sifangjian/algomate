from algomate.api.v1.npcs import _parse_json_field, RECOMMENDED_LEARNING_PATH, VALID_ALGORITHM_TYPES, DEFAULT_NPCS

assert _parse_json_field('["a","b"]') == ["a", "b"], "parse valid json"
assert _parse_json_field("") == [], "parse empty string"
assert _parse_json_field(None) == [], "parse None"
assert _parse_json_field("invalid") == [], "parse invalid json"
assert len(RECOMMENDED_LEARNING_PATH) == 8, "learning path has 8 steps"
assert len(VALID_ALGORITHM_TYPES) == 8, "8 valid algorithm types"
assert len(DEFAULT_NPCS) == 8, "8 default NPCs"
assert DEFAULT_NPCS[0]["name"] == "老夫子", "first NPC is 老夫子"
assert DEFAULT_NPCS[0]["algorithm_type"] == "basic_data_structure", "first NPC type"
assert RECOMMENDED_LEARNING_PATH[0]["npc_name"] == "老夫子", "first step is 老夫子"
assert "basic_data_structure" in VALID_ALGORITHM_TYPES, "basic_data_structure is valid"
assert "invalid_type" not in VALID_ALGORITHM_TYPES, "invalid_type is not valid"
print("All 11 backend unit tests PASSED!")
