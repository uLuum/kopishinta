document.addEventListener("DOMContentLoaded", () => {
    const toLabel = document.getElementById("to-label");
    const downloadBtn = document.getElementById("download-btn");
    const totalInventoryEl = document.getElementById("total-inventory");
    const inventoryBody = document.getElementById("inventory-body");
    const todayTotalEl = document.getElementById("today-total");
    const yesterdayTotalEl = document.getElementById("yesterday-total");
    const weekTotalEl = document.getElementById("week-total");
    const monthTotalEl = document.getElementById("month-total");

    // Fungsi untuk mengambil data dari API
    async function fetchInventoryData() {
        try {
            const response = await fetch("/laporan/inventory/");
            if (!response.ok) {
                throw new Error("Gagal mengambil data inventory.");
            }

            const data = await response.json();
            console.log("Data inventory:", data.inventory); // Debugging
            updateTable(data.inventory);
            updateSoldTable(data);
            updateTotalTerjual(data.inventory);
        } catch (error) {
            console.error("Error:", error);
        }
    }

    // Fungsi untuk memperbarui tabel total terjual
    function updateSoldTable(data) {
        // Pastikan data tersedia sebelum digunakan
        const totalToday = data.total_today || 0; // Gunakan default 0 jika undefined
        const totalYesterday = data.total_yesterday || 0;
        const totalWeek = data.total_week || 0;
        const totalMonth = data.total_month || 0;
    
        // Perbarui elemen HTML dengan nilai yang telah dihitung
        todayTotalEl.textContent = totalToday.toLocaleString();
        yesterdayTotalEl.textContent = totalYesterday.toLocaleString();
        weekTotalEl.textContent = totalWeek.toLocaleString();
        monthTotalEl.textContent = totalMonth.toLocaleString();
    }    

    // Fungsi untuk memperbarui tabel
    function updateTable(data) {
        inventoryBody.innerHTML = ""; // Kosongkan tabel
        data.forEach((item) => {
            const row = `
                <tr>
                    <td>${item.tanggal}</td>
                    <td>${item.nomor_order}</td>
                    <td>${item.sku}</td>
                    <td>${item.nama_item}</td>
                    <td>${item.terjual}</td>
                </tr>
            `;
            inventoryBody.insertAdjacentHTML("beforeend", row);
        });
    }

    // Fungsi untuk memperbarui total item terjual
    function updateTotalTerjual(data) {
        const total = data.reduce((sum, item) => sum + item.terjual, 0);
        totalInventoryEl.textContent = total.toLocaleString();
    }

    // Ekspor data ke CSV
    downloadBtn.addEventListener("click", () => {
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Tanggal,Nomor Order,SKU,Nama Item,Terjual\n";

        const rows = Array.from(inventoryBody.querySelectorAll("tr"));
        rows.forEach((row) => {
            const cells = Array.from(row.querySelectorAll("td"));
            const rowData = cells.map((cell) => cell.textContent.trim()).join(",");
            csvContent += rowData + "\n";
        });

        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "laporan_inventory.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });

    // Ambil data awal
    fetchInventoryData();
});
