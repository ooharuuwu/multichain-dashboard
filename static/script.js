
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".pool-card").forEach(card => {
        card.addEventListener("click", () => {
            const poolid = card.dataset.pool
            
                window.location.href = `/graph/${poolid}`;
            });
        })
    })
