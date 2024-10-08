(function () {
  class EventSeatCanvas extends AbstractSeatCanvas {
    constructor(canvasElem, params) {
      super(canvasElem, params.cellSize);

      this.pickedColor = params.pickedColor;
      this.oldSeats = params.oldSeats;

      this.currentSeats = [];
    }

    isOccupied(gridX, gridY) {
      return this.isOccupiedIn(this.currentSeats, gridX, gridY);
    }

    redrawSeats() {
      this.redrawSeatArray(this.currentSeats, this.pickedColor);
    }

    onDragCell(event, gridX, gridY) {
      if (this.mouseDragStartedOnOccupiedCell) {
        this.addSeat(this.currentSeats, gridX, gridY);
      } else {
        this.removeSeat(this.currentSeats, gridX, gridY);
      }
    }

    onClickCell(event, gridX, gridY) {
      if (this.isOccupiedIn(this.currentSeats, gridX, gridY)) {
        this.removeSeat(this.currentSeats, gridX, gridY);
      } else {
        this.addSeat(this.currentSeats, gridX, gridY);
      }
    }

    initSeats() {
      for (let seat of this.oldSeats) {
        this.addSeat(this.currentSeats, seat[0], seat[1]);
      }
    }
  }

  window.addEventListener('load', () => {
    // read parameters from the hidden input field
    let params = JSON.parse(document.getElementById("id_canvas_params").value)
    let canvas = document.getElementById("seat_canvas");

    let seatCanvas = new EventSeatCanvas(canvas, params);

    // set up form submission hook
    let seatsInput = document.getElementById("id_seats");
    let form = document.getElementById("event_form");
    form.addEventListener("submit", event => {
      let seats = JSON.stringify(seatCanvas.currentSeats);
      seatsInput.setAttribute("value", seats);
    });

    seatCanvas.init();
  });
})();
