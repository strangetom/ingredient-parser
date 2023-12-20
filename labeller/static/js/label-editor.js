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

document.addEventListener("DOMContentLoaded", () => {
  let labelSelects = document.querySelectorAll("select");
  labelSelects.forEach((el) => {
    el.addEventListener("change", setCellColor);
  });
});
