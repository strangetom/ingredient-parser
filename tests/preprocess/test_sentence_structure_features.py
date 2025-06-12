from ingredient_parser.en import PreProcessor


class Test_multi_ingredient_phrase_features:
    def test_multi_ingredient_phrase_detection(self):
        """
        Test that multi ingredient phrase is correctly identified.
        """
        p = PreProcessor("2 tbsp chicken or beef stock")
        assert p.sentence_structure.phrases == [[2, 3, 4, 5]]

    def test_multi_ingredient_phrase_detection_with_name_mod(self):
        """
        Test that multi ingredient phrase with name modifier is correctly identified.
        """
        p = PreProcessor("2 tbsp hot chicken or beef stock")
        assert p.sentence_structure.phrases == [[2, 3, 4, 5, 6]]

    def test_extended_multi_ingredient_phrase_detection(self):
        """
        Test that extended multi ingredient phrase is correctly identified.
        """
        p = PreProcessor("2 tbsp olive, vegetable or sunflower oil")
        assert p.sentence_structure.phrases == [[2, 3, 4, 5, 6, 7]]

    def test_mip_start_feature_unit(self):
        """
        Test that the start of the multi ingredient phrase is correctly identified by
        ignoring the units.
        """
        p = PreProcessor("2 tbsp olive, vegetable or sunflower oil")

        # Assert that only the 3rd token has the `mip_start` feature.
        for i, token_features in enumerate(p.sentence_features()):
            if i == 2:
                assert token_features.get("mip_start", False)
            else:
                assert not token_features.get("mip_start", False)

    def test_mip_start_feature_size(self):
        """
        Test that the start of the multi ingredient phrase is correctly identified by
        ignoring the size.
        """
        p = PreProcessor("1 large sweet or Yukon Gold potato")

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
        p = PreProcessor("2 tbsp hot chicken or beef stock")

        # Assert that only the last token has the `mip_end` feature.
        for i, token_features in enumerate(p.sentence_features()):
            if i == len(p.sentence_features()) - 1:
                assert token_features.get("mip_end", False)
            else:
                assert not token_features.get("mip_end", False)


class Test_compound_sentence_features:
    def test_detect_compound_sentence_number_unit(self):
        """
        Test that the or-number-unit sequence is identified as split point.
        """
        p = PreProcessor("2 tbsp oil or 1 cup butter")
        assert p.sentence_structure.sentence_splits == [3]

    def test_detect_compound_sentence_double_number_unit(self):
        """
        Test that the or-number-number-unit sequence is identified as split point.
        """
        p = PreProcessor("1 1/4 cups squash, or 1 10-ounce package frozen squash")
        assert p.sentence_structure.sentence_splits == [4]

    def test_detect_compound_sentence_number_noun(self):
        """
        Test that the or-number-noun sequence is identified as split point.
        """
        p = PreProcessor("2 serrano peppers or 1 jalapeño pepper")
        assert p.sentence_structure.sentence_splits == [3]

    def test_detect_compound_sentence_number_size(self):
        """
        Test that the or-number-size sequence is identified as split point.
        """
        p = PreProcessor("2 small carrots or 1 large carrot")
        assert p.sentence_structure.sentence_splits == [3]

    def test_detect_compound_sentence_multiple_splits(self):
        """
        Test that all or-number-noun sequences are identified as split points.
        """
        p = PreProcessor(
            "2 medium-ripe tomatoes or 4 plum tomatoes or 8 to 10 cherry tomatoes"
        )
        assert p.sentence_structure.sentence_splits == [3, 7]
