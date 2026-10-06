const searchInput = document.querySelector('[data-search-input]');

if (searchInput) {
  const rows = [...document.querySelectorAll('[data-search-row]')];
  const count = document.querySelector('[data-search-count]');
  const empty = document.querySelector('[data-no-results]');

  const normalize = (value) => value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase();

  searchInput.addEventListener('input', () => {
    const term = normalize(searchInput.value.trim());
    let visible = 0;

    rows.forEach((row) => {
      const found = normalize(row.textContent).includes(term);
      row.hidden = !found;
      if (found) visible += 1;
    });

    count.textContent = visible + (visible === 1 ? ' exibido' : ' exibidos');
    empty.hidden = visible !== 0;
  });
}
