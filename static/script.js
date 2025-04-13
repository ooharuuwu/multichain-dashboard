

document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".pool-card").forEach(card => {
      card.addEventListener("click", () => {
        const poolid = card.dataset.pool;
        window.location.href = `/graph/${poolid}`;
      });
    });
  
    const sortSelect = document.getElementById("sort-select");
    if (sortSelect) {

      sortSelect.addEventListener("change", function () {
        document.getElementById("filter-form").submit();

      });
    }

    const searchInput = document.getElementById("live-search")
    if(searchInput) {
        searchInput.addEventListener("input", function() {
            const query = this.value.toLowerCase().trim().split(" ");

            document.querySelectorAll(".pool-card").forEach(card =>{
                const project = card.dataset.project || "";
                const symbol = card.dataset.symbol || "";

                const matches = query.every(term =>
                    project.includes(term) || symbol.includes(term)
                )
                card.style.display = matches ? "" : "none";
            })
        })
    }

    const alertForm = document.querySelector('form[action="/setalert"]')
    if (alertForm) {
        alertForm.addEventListener("submit", function (e) {
            const protocol = document.getElementById("protocol").value
            const threshold = document.querySelector('input[name="threshold"]').value

            if (!protocol || !threshold) {
                e.preventDefault();
                alert("Please select protocol and threshold")
            }
        })
    }
  });