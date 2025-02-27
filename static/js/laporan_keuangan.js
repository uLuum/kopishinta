document.addEventListener('DOMContentLoaded', () => {
    const toLabel = document.getElementById("to-label");
    const totalPendapatanElem = document.getElementById("total-pendapatan");
    const downloadBtn = document.getElementById("download-btn");
    const yesterdayTotalElem = document.getElementById("yesterday-total");
    const todayTotalElem = document.getElementById("today-total");
    const weekTotalElem = document.getElementById("week-total");
    const monthTotalElem = document.getElementById("month-total");

    let laporanData = []; // Data akan diisi secara dinamis

    // Fungsi untuk mengambil data dari server
    async function fetchLaporanData() {
        try {
            const response = await fetch('/api/laporan/keuangan/'); // Endpoint Django
            if (!response.ok) {
                throw new Error("Gagal mengambil data laporan keuangan.");
            }
            const data = await response.json();
            laporanData = data.laporan;
            updateTable(laporanData);
            updateTotalPendapatan(laporanData);
            updateBillingTable(laporanData);
        } catch (error) {
            console.error("Error:", error);
        }
    }

    // Panggil fungsi fetch data
    fetchLaporanData();

    // Fungsi untuk update tabel
    function updateTable(data) {
        const tableBody = document.getElementById("laporan-body");
        tableBody.innerHTML = "";

        data.forEach(item => {
            const row = `
                <tr>
                    <td>${item.tanggal}</td>
                    <td>${item.nomor_order}</td>
                    <td>${item.layanan}</td>
                    <td>${item.total_harga}</td>
                    <td>${item.metode_pembayaran}</td>
                    <td>${item.status_bayar}</td>
                </tr>
            `;
            tableBody.innerHTML += row;
        });
    }

    // Fungsi untuk update total pendapatan
    function updateTotalPendapatan(data) {
        console.log("Data untuk perhitungan total pendapatan:", data); // Debugging
        const total = data.reduce((sum, item) => {
            const harga = Number(item.total_harga.replace('Rp', '').replace('.', '').trim());
            console.log(`Menambahkan ${harga} ke total ${sum}`); // Debugging setiap iterasi
            return sum + harga;
        }, 0);
        totalPendapatanElem.textContent = `Rp ${total.toLocaleString('id-ID')}`; // Tampilkan format Rupiah
    }
    
    function parseDate(dateStr) {
        const [day, month, yearAndTime] = dateStr.split('-');
        const [year, time] = yearAndTime.split(' ');
        const [hour, minute] = time.split(':');
        return new Date(year, month - 1, day, hour, minute); // Bulan di JS dimulai dari 0
    }

    // Fungsi untuk update tabel Pendapatan (Billing)
    function updateBillingTable(data) {
        const today = new Date();
        const startOfToday = new Date(today.getFullYear(), today.getMonth(), today.getDate());
        const startOfYesterday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1); // Awal hari kemarin
        const endOfYesterday = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 1, 23, 59, 59); // Akhir hari kemarin
        const startOfWeek = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 7);
        const startOfMonth = new Date(today.getFullYear(), today.getMonth(), today.getDate() - 30);

        let todayTotal = 0;
        let yesterdayTotal = 0;
        let weekTotal = 0;
        let monthTotal = 0;

        data.forEach(item => {
            const dataTanggal = parseDate(item.tanggal);
            const harga = Number(item.total_harga.replace(/[^\d]/g, "")); // Pastikan angka diambil dengan benar

            if (dataTanggal >= startOfToday) {
                todayTotal += harga;
            }
            if (dataTanggal >= startOfYesterday && dataTanggal <= endOfYesterday) {
                yesterdayTotal += harga; // Akumulasi untuk kemarin
            }
            if (dataTanggal >= startOfWeek) {
                weekTotal += harga;
            }
            if (dataTanggal >= startOfMonth) {
                monthTotal += harga;
            }
        });

        todayTotalElem.textContent = `Rp ${todayTotal.toLocaleString('id-ID')}`;
        yesterdayTotalElem.textContent = `Rp ${yesterdayTotal.toLocaleString('id-ID')}`; // Update kolom Kemarin
        weekTotalElem.textContent = `Rp ${weekTotal.toLocaleString('id-ID')}`;
        monthTotalElem.textContent = `Rp ${monthTotal.toLocaleString('id-ID')}`;
    }

    // Fungsi untuk ekspor data ke CSV
    downloadBtn.addEventListener("click", () => {
        let csvContent = "data:text/csv;charset=utf-8,";
        csvContent += "Tanggal,Nomor Order,Layanan,Total Harga,Metode Pembayaran,Status Bayar\n";
    
        laporanData.forEach(item => {
            const row = `${item.tanggal},${item.nomor_order},${item.layanan},${item.total_harga},${item.metode_pembayaran},${item.status_bayar}`;
            csvContent += row + "\n";
        });
    
        const encodedUri = encodeURI(csvContent);
        const link = document.createElement("a");
        link.setAttribute("href", encodedUri);
        link.setAttribute("download", "laporan_keuangan.csv");
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    });    

});