from ingredient_parser.en import PreProcessor


class Test_multi_ingredient_phrase_features:
    def test_multi_ingredient_phrase_detection(self):
        """
        Test that multi ingredient phrase is correctly identified.
        """
        p = PreProcessor("2 tbsp chicken or beef stock", custom_units={})
        assert p.sentence_structure.mip_phrases == [([2, 3, 4, 5], "MIP")]

    def test_multi_ingredient_phrase_detection_with_name_mod(self):
        """
        Test that multi ingredient phrase with name modifier is correctly identified.
        """
        p = PreProcessor("2 tbsp hot chicken or beef stock", custom_units={})
        assert p.sentence_structure.mip_phrases == [([2, 3, 4, 5, 6], "MIP")]

    def test_extended_multi_ingredient_phrase_detection(self):
        """
        Test that extended multi ingredient phrase is correctly identified.
        """
        p = PreProcessor("2 tbsp olive, vegetable or sunflower oil", custom_units={})
        assert p.sentence_structure.mip_phrases == [([2, 3, 4, 5, 6, 7], "EMIP")]

    def test_extended_multi_ingredient_phrase_detection_comma(self):
        """
        Test that extended multi ingredient phrase containing two commas is correctly
        identified.
        """
        p = PreProcessor("2 tbsp olive, vegetable, or sunflower oil", custom_units={})
        assert p.sentence_structure.mip_phrases == [([2, 3, 4, 5, 6, 7, 8], "EMIP")]

    def test_multi_ingredient_phrase_detection_determinant(self):
        """
        Test that multi ingredient phrase containing a determinant is correctly
        identified.
        """
        p = PreProcessor("½ c grapeseed oil or any mild-flavored oil", custom_units={})
        assert p.sentence_structure.mip_phrases == [([2, 3, 4, 5, 6, 7], "MIP")]

    def test_multi_ingredient_phrase_detection_and_or(self):
        """
        Test that multi ingredient phrase  using "and/or" is correctly identified.
        """
        p = PreProcessor("2 tbsp red and/or white wine", custom_units={})
        assert p.sentence_structure.mip_phrases == [([2, 3, 4, 5], "MIP")]

    def test_mip_start_feature_unit(self):
        """
        Test that the start of the multi ingredient phrase is correctly identified by
        ignoring the units.
        """
        p = PreProcessor("2 tbsp olive, vegetable or sunflower oil", custom_units={})

        # Assert that only the 3rd token has the `mip_start` feature.
        for i, token_features in enumerate(p.sentence_features()):
            if i == 2:
                assert token_features.get("mip_start", False)
            else:
                assert not token_features.get("mip_start", False)

    def test_mip_start_feature(self):
        """
        Test that the start of the multi ingredient phrase is correctly identified by
        ignoring the size.
        """
        p = PreProcessor("1 large sweet or Yukon Gold potato", custom_units={})

        # Assert that only the 3rd token has the `mip_start` feature.
        for i, token_features in enumerate(p.sentence_features()):
            if i == 2:
                assert token_features.get("mip_start", False)
            else:
                assert not token_features.get("mip_start", False)

    def test_mip_end_feature(self):
        """
        Test that the end of the multi ingredient phrase is correctly identified.
        """
        p = PreProcessor("2 tbsp hot chicken or beef stock", custom_units={})

        # Assert that only the last token has the `mip_end` feature.
        for i, token_features in enumerate(p.sentence_features()):
            if i == len(p.sentence_features()) - 1:
                assert token_features.get("mip_end", False)
            else:
                assert not token_features.get("mip_end", False)

    def test_within_mip_feature(self):
        """
        Test that the all tokens within the multi-ingredient phrase have the
        within_mip feature set to True.
        """
        p = PreProcessor("2 tbsp hot chicken or beef stock", custom_units={})

        # Assert that all tokens after the first two have the within_mip feature.
        for i, token_features in enumerate(p.sentence_features()):
            if i > 1:
                assert token_features.get("within_mip", False)
            else:
                assert not token_features.get("within_mip", False)

    def test_within_mip_clause_feature_mip(self):
        """
        Test that the all tokens within the first clause of the MIP have the
        within_mip_clause_-1 feature.
        """
        p = PreProcessor("2 tbsp chicken or beef stock", custom_units={})

        # Assert that all tokens after the first two have the within_mip feature.
        for i, token_features in enumerate(p.sentence_features()):
            if i == 2:
                assert token_features.get("within_mip_clause_-1", False)
            else:
                assert not token_features.get("within_mip_clause_-1", False)

    def test_within_mip_clause_feature_emip(self):
        """
        Test that the all tokens within the two clauses have the appropriate
        with_mip_clause_* feature.
        """
        p = PreProcessor("2 tbsp olive, vegetable or sunflower oil", custom_units={})

        # Assert that all tokens after the first two have the within_mip_clause feature.
        for i, token_features in enumerate(p.sentence_features()):
            if i == 2:
                assert token_features.get("within_mip_clause_-2", False)
            elif i == 4:
                assert token_features.get("within_mip_clause_-1", False)
            elif i in [6, 7]:
                assert token_features.get("within_mip_clause_0", False)
            else:
                assert not token_features.get("within_mip_clause_-1", False)
                assert not token_features.get("within_mip_clause_-2", False)
                assert not token_features.get("within_mip_clause_0", False)


class Test_compound_sentence_features:
    def test_detect_compound_sentence_number_unit(self):
        """
        Test that the or-number-unit sequence is identified as split point.
        """
        p = PreProcessor("2 tbsp oil or 1 cup butter", custom_units={})
        assert p.sentence_structure.sentence_splits == [3]

    def test_detect_compound_sentence_double_number_unit(self):
        """
        Test that the or-number-number-unit sequence is identified as split point.
        """
        p = PreProcessor(
            "1 1/4 cups squash, or 1 10-ounce package frozen squash", custom_units={}
        )
        assert p.sentence_structure.sentence_splits == [4]

    def test_detect_compound_sentence_number_noun(self):
        """
        Test that the or-number-noun sequence is identified as split point.
        """
        p = PreProcessor("2 serrano peppers or 1 jalapeño pepper", custom_units={})
        assert p.sentence_structure.sentence_splits == [3]

    def test_detect_compound_sentence_number_size(self):
        """
        Test that the or-number-size sequence is identified as split point.
        """
        p = PreProcessor("2 small carrots or 1 large carrot", custom_units={})
        assert p.sentence_structure.sentence_splits == [3]

    def test_detect_compound_sentence_multiple_splits(self):
        """
        Test that all or-number-noun sequences are identified as split points.
        """
        p = PreProcessor(
            "2 medium-ripe tomatoes or 4 plum tomatoes or 8 to 10 cherry tomatoes",
            custom_units={},
        )
        assert p.sentence_structure.sentence_splits == [3, 7]

    def test_detect_no_compound_sentence_alternative_units(self):
        """
        Test that no split is identified despite the or-number-unit sequence because the
        prior token is also a unit.
        """
        p = PreProcessor(
            "3 cups or 1 lb thinly sliced leeks including the tender green",
            custom_units={},
        )
        assert p.sentence_structure.sentence_splits == []

    def test_after_sentence_split_feature(self):
        """
        Test that the or-number-size sequence is identified as split point.
        """
        p = PreProcessor("2 small carrots or 1 large carrot", custom_units={})

        # Assert that only the tokens after 3 have after_sentence_split feature.
        for i, token_features in enumerate(p.sentence_features()):
            if i >= 3:
                assert token_features.get("after_sentence_split", False)
            else:
                assert not token_features.get("after_sentence_split", False)


class Test_example_phrase_features:
    def test_example_phrase_detection_like(self):
        """
        Test phrase using "like" is detected
        """
        p = PreProcessor(
            "2 tbsp chopped fresh herbs, like parsley and chives", custom_units={}
        )
        assert p.sentence_structure.example_phrases == [[6, 7, 8, 9]]

    def test_example_phrase_detection_such_as(self):
        """
        Test phrase using "such as" is detected
        """
        p = PreProcessor(
            "2 tbsp chopped fresh herbs, such as parsley and chives", custom_units={}
        )
        assert p.sentence_structure.example_phrases == [[6, 7, 8, 9, 10]]

    def test_example_phrase_detection_eg(self):
        """
        Test phrase using "e.g." is detected
        """
        p = PreProcessor(
            "2 tbsp chopped fresh herbs, e.g. parsley and chives", custom_units={}
        )
        assert p.sentence_structure.example_phrases == [[6, 7, 8, 9]]

    def test_example_phrase_detection_invalid_start_adjective(self):
        """
        Test phrase starting with invalid adjective is detected, and invalid adjective
        is removed from phrase indices.
        """
        p = PreProcessor(
            "1 bottle dry red wine, heavy and coarse like a Zinfandel", custom_units={}
        )
        assert p.sentence_structure.example_phrases == [[9, 10, 11]]

    def test_example_phrase_detection_multiple_examples(self):
        """
        Test both phrases using "like" are detected.
        """
        p = PreProcessor(
            "2 cups ale, like Boddingtons, or lager, like Carlsburg", custom_units={}
        )
        assert p.sentence_structure.example_phrases == [[4, 5], [10, 11]]

    def test_example_phrase_detection_duplicate_examples(self):
        """
        Test phrase using "like" are detected when both phrases are identical (in both
        token text and part of speech tag).
        """
        p = PreProcessor(
            "2 cups ale, like Carlsburg, or lager, like Carlsburg", custom_units={}
        )
        assert p.sentence_structure.example_phrases == [[4, 5], [10, 11]]

    def test_example_phrase_detection_feature(self):
        """
        Test that the example_phrase feature is correct set.
        """
        p = PreProcessor(
            "1 bottle dry red wine, heavy and coarse like a Zinfandel", custom_units={}
        )

        # Assert that only the tokens after 8 have example_phrase feature set True.
        for i, token_features in enumerate(p.sentence_features()):
            if i >= 9:
                assert token_features.get("example_phrase", False)
            else:
                assert not token_features.get("example_phrase", False)

    def test_example_phrase_detection_no_conjunction(self):
        """
        Test phrase using "such as" is detected in a sentence with no conjunction.
        This is to protect against a bug introduced in
        24a83905df84ffc8910f6d532f4b8f3073321970 and fixed in
        23a8ae788b01b816eba9f73a2ca2fe864482bf36 which prevent example phrase detection
        on sentence that did not include a "CC" tag. All the example phrase tests at
        the time contained a "CC" tag by coincidence so the bug was not noticed at
        the time.
        """
        p = PreProcessor("5 oz passion fruit liqueur, such as Aliz", custom_units={})
        assert p.sentence_structure.example_phrases == [[6, 7, 8]]


class Test_dimensional_phrase_features:
    def test_dimensional_phrase_detection(self):
        """
        Test dimensional phrase comprising number-unit-dimension is detected.
        """
        p = PreProcessor("1 2 in thick piece of steak", custom_units={})
        assert p.sentence_structure.dimensional_phrases == [[1, 2, 3]]

    def test_dimensional_phrase_no_dimension(self):
        """
        Test dimensional phrase comprising number-unit is detected.
        """
        p = PreProcessor("2in/5cm piece of ginger", custom_units={})
        assert p.sentence_structure.dimensional_phrases == [[0, 1, 2, 3, 4]]

    def test_dimensional_phrase_with_parenthesis(self):
        """
        Test dimensional phrase comprising two pair of number-unit, with the second pair
        in parentheses, followed by a dimension is detected.
        """
        p = PreProcessor("1 2 in (5 cm) long piece of steak", custom_units={})
        assert p.sentence_structure.dimensional_phrases == [[1, 2, 3, 4, 5, 6, 7]]

    def test_dimensional_phrase_with_slash(self):
        """
        Test dimensional phrase comprising two pair of number-unit, with the second pair
        after a forward slash, followed by a dimension is detected.
        """
        p = PreProcessor("1 2 in / 5 cm wide piece of steak", custom_units={})
        assert p.sentence_structure.dimensional_phrases == [[1, 2, 3, 4, 5, 6]]

    def test_dimensional_phrase_with_preposition(self):
        """
        Test dimensional phrase comprising number-unit-"in"-dimension is detected.
        """
        p = PreProcessor("1 potato, 3 inches in diameter", custom_units={})
        assert p.sentence_structure.dimensional_phrases == [[3, 4, 5, 6]]


class Test_segment_features:
    def test_simple_sentence(self):
        """
        Test basic segment features for a simple sentence with 1 segment.
        """
        p = PreProcessor("1 cup flour")
        segment_features = p.sentence_structure.segment_features

        assert all(t.segment == 0 for t in p.tokenized_sentence)
        assert [feat.get("segment_position") for feat in segment_features] == [
            "FIRST",
            "MID",
            "LAST",
        ]
        assert [feat.get("segment_length") for feat in segment_features] == [
            "3-4",
            "3-4",
            "3-4",
        ]
        assert [feat.get("segment_starts_with_qty") for feat in segment_features] == [
            True,
            True,
            True,
        ]

    def test_multiple_segments(self):
        """
        Test segment features for a sentence with multiple segments.
        """
        p = PreProcessor(
            "2 cups cubes made from crusty bread, such as a baguette, toasted"
        )
        segments = [t.segment for t in p.tokenized_sentence]
        segment_features = p.sentence_structure.segment_features

        assert segments == [0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1, 1, 1, 2]

        # Tokens 7 and 12 are a segment separators.
        for idx in [7, 12]:
            assert segment_features[idx].get("segment_position") == "SEP"
            assert "segment_starts_with_qty" not in segment_features[idx].keys()
            assert "qty_in_earlier_segment" not in segment_features[idx].keys()

        # segment_starts_with_qty is True for first segment only
        assert segment_features[0].get("segment_starts_with_qty")
        assert not segment_features[8].get("segment_starts_with_qty")
        assert not segment_features[13].get("segment_starts_with_qty")

        # qty_in_earlier_segment is True for 2nd and 3rd segment and not present for 1st
        assert "qty_in_earlier_segment" not in segment_features[0].keys()
        assert segment_features[8].get("qty_in_earlier_segment")
        assert segment_features[13].get("qty_in_earlier_segment")


class Test_parenthesis_span_features:
    def test_no_parentheses(self):
        """
        Test that sentence with no parentheses will generate no paren span features.
        """
        p = PreProcessor("1 cup flour")
        assert p.sentence_structure.paren_span_features == [{}, {}, {}]

    def test_single_parenthesis_span(self):
        """
        Test that sentence with single parenthesis spans has features set for tokens in
        span.
        """
        p = PreProcessor("3 (14 ounce) cans chicken broth")
        paren_span_features = p.sentence_structure.paren_span_features

        assert [t.paren_depth for t in p.tokenized_sentence] == [0, 1, 1, 1, 1, 0, 0, 0]

        # Tokens with paren_depth == 0 should not have features
        for i, token in enumerate(p.tokenized_sentence):
            if token.paren_depth == 0:
                assert paren_span_features[i] == {}

        # paren_first_pos should be same as POS tag of first token in paren span
        for idx in [2, 3]:
            assert (
                paren_span_features[idx].get("paren_first_pos")
                == p.tokenized_sentence[2].pos_tag
            )

    def test_multiple_parenthesis_span(self):
        """
        Test that sentence with multiple parenthesis spans has features set for tokens
        in spans.
        """
        p = PreProcessor("3 (14 ounce) cans chicken broth [or stock]")
        paren_span_features = p.sentence_structure.paren_span_features

        assert [t.paren_depth for t in p.tokenized_sentence] == [
            0,
            1,
            1,
            1,
            1,
            0,
            0,
            0,
            1,
            1,
            1,
            1,
        ]

        # Tokens with paren_depth == 0 should not have features
        for i, token in enumerate(p.tokenized_sentence):
            if token.paren_depth == 0:
                assert paren_span_features[i] == {}

        # paren_first_pos should be same as POS tag of first token in each paren span
        for idx in [2, 3]:
            assert (
                paren_span_features[idx].get("paren_first_pos")
                == p.tokenized_sentence[2].pos_tag
            )
        for idx in [9, 10]:
            assert (
                paren_span_features[idx].get("paren_first_pos")
                == p.tokenized_sentence[9].pos_tag
            )
