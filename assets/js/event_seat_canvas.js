window.addEventListener('load', () => {
  // read parameters from the hidden input field
  let params = JSON.parse(document.getElementById("id_canvas_params").value)
  let canvas = document.getElementById("seat_canvas");

  let seatCanvas = new SeatCanvas(canvas, params.cellSize, params.pickedColor, params.oldSeats);

  // set up form submission hook
  let seatsInput = document.getElementById("id_seats");
  let form = document.getElementById("event_form");
  form.addEventListener("submit", event => {
    let seats = JSON.stringify(seatCanvas.currentSeats);
    seatsInput.setAttribute("value", seats);
  });

  seatCanvas.init();
});

