document.addEventListener('DOMContentLoaded', function () {
  setTimeout(function () {
    var alerts = document.querySelectorAll('.alert');
    alerts.forEach(function (alert) {
      alert.style.transition = 'opacity 0.4s';
      alert.style.opacity = '0';
      setTimeout(function () { alert.remove(); }, 400);
    });
  }, 3000);

  var salaryTypeRadios = document.querySelectorAll('input[name="salary_type"]');
  var salaryDayGroup = document.getElementById('salary-day-group');
  if (salaryTypeRadios.length && salaryDayGroup) {
    function updateSalaryDayVisibility() {
      var checked = document.querySelector('input[name="salary_type"]:checked');
      if (checked && checked.value === 'fixed') {
        salaryDayGroup.style.display = 'block';
      } else {
        salaryDayGroup.style.display = 'none';
      }
    }
    salaryTypeRadios.forEach(function (r) {
      r.addEventListener('change', updateSalaryDayVisibility);
    });
    updateSalaryDayVisibility();
  }
});
