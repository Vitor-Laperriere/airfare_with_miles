flatpickr("input[type='date']", {
    minDate: "today",
    maxDate: new Date().fp_incr(329),
    dateFormat: "d/m/Y",
    locale: "pt"
});