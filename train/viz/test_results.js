document.addEventListener("DOMContentLoaded", () => {
	const filterDialog = document.querySelector("#filter-dialog");
	const filterDialogBtn = document.querySelector("#filters-btn");
	filterDialogBtn.addEventListener("click", () => {
		filterDialog.showModal();
	});
	filterDialog.addEventListener("click", (event) => {
		if (event.target.nodeName === "DIALOG") {
			filterDialog.returnValue = "cancel";
			filterDialog.close();
		}
	});

	const copyButtons = document.querySelectorAll("button.copy");
	copyButtons.forEach((button) => {
		button.addEventListener("click", (e) => {
			let text = e.target.previousElementSibling.innerText;
			// Strip off source from beginning
			text = text.substring(text.indexOf(" ") + 1);
			navigator.clipboard.writeText(text);
		});
	});
	const selectAllButtons = document.querySelectorAll("button.select-all");
	selectAllButtons.forEach((button) => {
		button.addEventListener("click", (e) => {
			const parent = e.target.parentElement;
			const checkboxes = parent.querySelectorAll("input[type='checkbox']");
			checkboxes.forEach((box) => (box.checked = true));
			applyFilter();
		});
	});
	function applyFilter() {
		const filtered_src = {};
		const sentences = document.querySelectorAll(".wrapper");

		const mismatch_filters = [...document.querySelectorAll("input.mismatch")]
			.filter((el) => el.checked)
			.map((el) => el.dataset.value);

		const src_filters = [...document.querySelectorAll("input.src")]
			.filter((el) => el.checked)
			.map((el) => el.dataset.value);

		let error_filters = [...document.querySelectorAll("input.error")]
			.filter((el) => el.checked)
			.map((el) => el.dataset.value);
		error_filters = new Set(error_filters);

		let token_filters = document
			.querySelector("#token-filter")
			.value.split(" ")
			.map((token) => token.toLowerCase());
		if (token_filters == "") {
			token_filters = new Set();
		} else {
			token_filters = new Set(token_filters);
		}

		sentences.forEach((sent) => {
			const sentence_tokens = [
				...sent.querySelectorAll("tr:first-of-type > td"),
			].map((td) => td.innerText.toLowerCase());
			sent_tokens = new Set(sentence_tokens);

			const errors = new Set(sent.dataset.errors.split(","));
			if (
				mismatch_filters.includes(sent.dataset.mismatches) &&
				src_filters.includes(sent.dataset.src) &&
				errors.intersection(error_filters).size > 0 &&
				(token_filters.size == 0 ||
					sent_tokens.intersection(token_filters).size == token_filters.size)
			) {
				sent.classList.remove("hidden");
				if (filtered_src[sent.dataset.src] == undefined) {
					filtered_src[sent.dataset.src] = 1;
				} else {
					filtered_src[sent.dataset.src] += 1;
				}
			} else {
				sent.classList.add("hidden");
			}
		});

		let total = 0;
		for (const [source, count] of Object.entries(filtered_src)) {
			document.querySelector(`span.display-count-${source}`).innerText = count;
			total += count;
		}
		document.querySelector("span.display-count-total").innerText = total;
	}
	const filterInputs = document.querySelectorAll("input[type='checkbox']");
	filterInputs.forEach((input) => {
		input.addEventListener("change", () => {
			applyFilter();
		});
	});
});
