(function () {
    const input = document.getElementById("globalSearchInput");
    const dropdown = document.getElementById("searchDropdown");
    if (!input || !dropdown) return;

    let cachedPosts = null;

    async function performSearch() {
        const query = input.value.toLowerCase().trim();
        if (!query) {
            dropdown.style.display = "none";
            return;
        }

        if (!cachedPosts) {
            const res = await fetch("/api/posts");
            const data = await res.json();
            cachedPosts = data.posts || [];
        }

        const matched = cachedPosts.filter(p =>
            p.title.toLowerCase().includes(query) || p.slug.toLowerCase().includes(query)
        ).slice(0, 6);

        dropdown.innerHTML = matched.length ? matched.map(p =>
            `<a href="${p.url}" class="dropdown-item">
                <span class="dropdown-title">${p.title}</span>
                <span class="dropdown-slug">${p.slug}</span>
             </a>`
        ).join("") : '<div class="dropdown-empty">Нічого не знайдено</div>';

        dropdown.style.display = "block";
    }

    input.addEventListener("input", performSearch);
    input.addEventListener("focus", performSearch);

    document.addEventListener("click", (e) => {
        if (!input.contains(e.target) && !dropdown.contains(e.target)) {
            dropdown.style.display = "none";
        }
    });

    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") {
            dropdown.style.display = "none";
        }
    });
})();