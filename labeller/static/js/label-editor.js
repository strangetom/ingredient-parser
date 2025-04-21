/**
 * Set table cell colour based on selected value in cell <select>
 * @param {[Event]} e <select> change event
 */
function setCellColor(e) {
  let select = e.target;
  let selected = select.options[select.selectedIndex].text;
  let cell = select.closest("td");

  cell.setAttribute("class", "");
  if (selected != "") {
    cell.classList.add(selected);
  }
}

/**
 * Save all data on page to server
 */
function save() {
  let dataset = document.querySelector("header h1").textContent;
  let data = {
    dataset: dataset,
    entries: [],
  };

  let entries = document.querySelectorAll(".entry");
  entries.forEach((entry) => {
    let rows = [...entry.querySelectorAll("tr")];
    let tokens = [...rows[0].querySelectorAll("td")].map(
      (el) => el.textContent.trim(),
    );
    let labels = [...rows[1].querySelectorAll("select")].map(
      (el) => el.options[el.selectedIndex].value,
    );


    data.entries.push({
      id: Number(entry.dataset.index),
      sentence: entry.querySelector(".sentence").textContent.trim(),
      tokens: tokens,
      labels: labels,
    });
  });

  let form = new FormData();
  form.append("data", JSON.stringify(data));
  fetch("/save", {
    method: "POST",
    body: form,
  })
    .then((res) => {
      let saveBtn = document.querySelector("#save-btn");
      if (res.ok) {
        saveBtn.classList.add("success");
        setTimeout(() => {
          saveBtn.classList.remove("success");
        }, 1500);
      } else {
        saveBtn.classList.add("failure");
        setTimeout(() => {
          saveBtn.classList.remove("failure");
        }, 1500);
      }
    })
    .catch((res) => {
      let saveBtn = document.querySelector("#save-btn");
      saveBtn.classList.add("failure");
      setTimeout(() => {
        saveBtn.classList.remove("failure");
      }, 1500);
    });
}

function remove(e) {
  let dataset = document.querySelector("header h1").textContent;
  let index = e.target.closest(".entry").dataset.index;

  if (confirm(`Delete entry ${index} from dataset?`)) {
    let url = new URL(`/delete/${index}`, location.href);
    fetch(url, {
      method: "GET",
    })
      .then((res) => {
        if (res.ok) {
          location.reload();
        } else {
          e.target.classList.add("failure");
          setTimeout(() => {
            e.target.classList.remove("failure");
          }, 1500);
        }
      })
      .catch((res) => {
        e.target.classList.add("failure");
        setTimeout(() => {
          e.target.classList.remove("failure");
        }, 1500);
      });
  }
}

function copy(e) {
  let sentence = e.target.previousElementSibling.innerText;
  navigator.clipboard.writeText(sentence);
}

document.addEventListener("DOMContentLoaded", () => {
  let labelSelects = document.querySelectorAll("select");
  labelSelects.forEach((el) => {
    el.addEventListener("change", setCellColor);
  });

  let deleteBtns = document.querySelectorAll("button.delete");
  deleteBtns.forEach((el) => {
    el.addEventListener("click", remove);
  });

  let copyBtns = document.querySelectorAll("button.copy");
  copyBtns.forEach((el) => {
    el.addEventListener("click", copy);
  });

  let saveBtn = document.querySelector("#save-btn");
  saveBtn.addEventListener("click", save);

  // Save on Ctrl+S keypress
  document.addEventListener("keydown", (e) => {
    if (e.ctrlKey && e.key === "s" || e.ctrlKey && e.key === "S") {
      e.preventDefault();
      save();
    }
  });
});
