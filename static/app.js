// 1. Fast search
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
        if (!input.contains(e.target) && !dropdown.contains(e.target)) dropdown.style.display = "none";
    });
    document.addEventListener("keydown", (e) => {
        if (e.key === "Escape") dropdown.style.display = "none";
    });
})();

// 2. Live Reload (SSE)
(function () {
    const currentSlug = document.body.dataset.slug;
    const nonSyncPages = ["map", "search", "diff"];

    if (currentSlug !== undefined && !nonSyncPages.includes(currentSlug)) {
        const evtSource = new EventSource("/api/live");
        evtSource.onmessage = function (event) {
            const data = JSON.parse(event.data);
            if (data.event === "update" && (data.slug === currentSlug || currentSlug === "")) {
                location.reload();
            }
        };
    }
})();