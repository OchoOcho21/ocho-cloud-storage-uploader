document.addEventListener('DOMContentLoaded', function() {
  showDashboard();
  fetchUserInfo();
});

function fetchUserInfo() {
  fetch('/accounts')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.accounts.length > 0) {
        const account = data.accounts[0];
        document.getElementById('navNickname').textContent = account.nickname || account.email;
      }
    })
    .catch(error => console.error('Error:', error));
}

function showDashboard() {
  fetch('/dashboard/content')
    .then(response => response.text())
    .then(html => {
      document.getElementById('dashboardContent').innerHTML = html;
      renderStorageChart();
    })
    .catch(error => console.error('Error:', error));
}

function renderStorageChart() {
  fetch('/accounts')
    .then(response => response.json())
    .then(data => {
      if (data.success && data.accounts.length > 0) {
        const account = data.accounts[0];
        const used = account.storage_used || 0;
        const total = account.storage_capacity || 1;
        const free = total - used;
        
        const ctx = document.getElementById('storageChart').getContext('2d');
        new Chart(ctx, {
          type: 'doughnut',
          data: {
            labels: ['Used', 'Free'],
            datasets: [{
              data: [used, free],
              backgroundColor: ['#4e73df', '#1cc88a'],
              hoverBackgroundColor: ['#2e59d9', '#17a673']
            }]
          },
          options: {
            maintainAspectRatio: false,
            plugins: {
              tooltip: {
                callbacks: {
                  label: function(context) {
                    const label = context.label || '';
                    const value = context.raw || 0;
                    return `${label}: ${formatBytes(value)}`;
                  }
                }
              },
              legend: {display: true, position: 'bottom'}
            },
            cutout: '80%'
          }
        });
        
        document.getElementById('storageInfo').innerHTML = `
          <h4>Storage Usage</h4>
          <p>Used: ${formatBytes(used)}</p>
          <p>Free: ${formatBytes(free)}</p>
          <p>Total: ${formatBytes(total)}</p>
        `;
      }
    });
}
