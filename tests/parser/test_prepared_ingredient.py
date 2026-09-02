from ingredient_parser import parse_ingredient


class Test_prepared_ingredient:
    def test_no_preparation(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is False
        """
        sentence = "3 cups (750 g) flour"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert not amount.PREPARED_INGREDIENT

    def test_preparation_between_amount_and_name(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is True
        """
        sentence = "3 cups (750 g) sifted flour"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

    def test_preparation_between_name_and_amount(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is True
        """
        sentence = "Onion, finely chopped (about 1 cup)"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

    def test_preparation_after_amount_and_name(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is False
        """
        sentence = "3 cups (750 g) flour, sifted"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert not amount.PREPARED_INGREDIENT

    def test_multiple_names(self):
        """
        Test that PREPARED_INGREDIENT for all amounts is True
        """
        sentence = "3 cups (750 ml) strained beef or vegetable stock"
        parsed = parse_ingredient(sentence)
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

    def test_irreversible_prep_volumetric(self):
        """
        Irreversible prep verb after a comma with a volumetric unit:
        pre-prep cup measurement is physically impossible, so the amount
        must measure the prepared form.
        """
        sentence = "1 cup carrots, diced"
        parsed = parse_ingredient(sentence)
        assert len(parsed.amount) > 0
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

    def test_irreversible_prep_volumetric_pair(self):
        """
        Override propagates across paired metric/imperial amounts via
        _distribute_related_flags. The override fires only on the cup
        (volumetric) but the gram (mass) gets True via propagation.
        """
        sentence = "1 cup (140 g) onion, finely chopped"
        parsed = parse_ingredient(sentence)
        assert len(parsed.amount) == 2
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

    def test_irreversible_prep_count_unit(self):
        """
        Override does not fire for count units. The count of whole
        ingredients is invariant under prep.
        """
        sentence = "3 carrots, diced"
        parsed = parse_ingredient(sentence)
        assert len(parsed.amount) > 0
        for amount in parsed.amount:
            assert not amount.PREPARED_INGREDIENT

    def test_irreversible_prep_mass_unit(self):
        """
        Override does not fire for mass units. Mass is preserved through
        irreversible prep so the flag is unchanged from the syntactic
        rule.
        """
        sentence = "1 lb chicken, cubed"
        parsed = parse_ingredient(sentence)
        assert len(parsed.amount) > 0
        for amount in parsed.amount:
            assert not amount.PREPARED_INGREDIENT

    def test_irreversible_prep_hyphenated(self):
        """
        Hyphenated PREP tokens (`thinly-sliced`) are split on hyphens so
        the irreversible head verb is still detected.
        """
        sentence = "1 cup carrots, thinly-sliced"
        parsed = parse_ingredient(sentence)
        assert len(parsed.amount) > 0
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

    def test_irreversible_prep_liquid_only_unit(self):
        """
        Override does not fire for strict-liquid volumetric units
        (ml, cl, dl, l, fl oz). Liquid volume is preserved through prep
        so the syntactic rule's False is the natural reading.
        """
        sentence = "10 ml olive oil, drained"
        parsed = parse_ingredient(sentence)
        assert len(parsed.amount) > 0
        for amount in parsed.amount:
            assert not amount.PREPARED_INGREDIENT

    def test_irreversible_prep_drained_volumetric(self):
        """
        `drained` produces a measurably different volume on solid /
        semi-solid ingredients (drained yogurt, drained beans). For
        non-liquid-only volumetric units the override correctly flips
        True.
        """
        sentence = "1 cup yogurt, drained"
        parsed = parse_ingredient(sentence)
        assert len(parsed.amount) > 0
        for amount in parsed.amount:
            assert amount.PREPARED_INGREDIENT

    def test_irreversible_prep_composite_amount(self):
        """
        The override has a separate fire site in
        _composite_amounts_pattern for lb+oz / pt+floz patterns. Verify
        a composite of pint+fl_oz with an irreversible verb flips both
        component amounts to True even though the fl_oz component alone
        is liquid-only.
        """
        sentence = "1 pint 3 fl oz tomatoes, diced"
        parsed = parse_ingredient(sentence)
        assert len(parsed.amount) > 0
        composite = parsed.amount[0]
        assert hasattr(composite, "amounts")
        assert len(composite.amounts) == 2
        for sub_amount in composite.amounts:
            assert sub_amount.PREPARED_INGREDIENT

    def test_excluded_verb_does_not_fire_override(self):
        """
        Pin the contract that verbs deliberately excluded from
        IRREVERSIBLE_PREP_VERBS (state adjectives, time-process verbs,
        reversible-order verbs) do not trigger the override even on
        volumetric units. Guards against accidental additions to the
        set that would silently change behavior.
        """
        sentence = "1 cup rice, cooked"
        parsed = parse_ingredient(sentence)
        assert len(parsed.amount) > 0
        for amount in parsed.amount:
            assert not amount.PREPARED_INGREDIENT
