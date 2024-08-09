let cellSize = 25;
let pickedColor = "blue";
let notPickedColor = "white";
let currentSeats = [];

function drawGrid() {
  const canvas = document.getElementById("seat_canvas");
  const ctx = canvas.getContext("2d");

  const gridCount = canvas.width / cellSize; // number of grid cells

  ctx.strokeStyle = 'black'; // color of the grid lines

  // draw the grid
  for (let i = 0; i <= gridCount; i++) {
    // vertical lines
    ctx.beginPath();
    ctx.moveTo(i * cellSize, 0);
    ctx.lineTo(i * cellSize, canvas.height);
    ctx.stroke();

    // horizontal lines
    ctx.beginPath();
    ctx.moveTo(0, i * cellSize);
    ctx.lineTo(canvas.width, i * cellSize);
    ctx.stroke();
  }
}

function redrawCanvas() {
  const canvas = document.getElementById("seat_canvas");
  const ctx = canvas.getContext("2d");

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  drawGrid();

  ctx.fillStyle = pickedColor;
  for (let seat of currentSeats) {
    let x = seat[0];
    let y = seat[1];
    ctx.fillRect(x * cellSize + 1, y * cellSize + 1, cellSize - 2, cellSize - 2);
  }
}

window.onload = function () {

  // set up form submission hook
  var form = document.getElementById("event_form");
  var seats_input = document.getElementById("id_seats");

  form.addEventListener("submit", event => {
    pixels = JSON.stringify(currentSeats);
    seats_input.setAttribute("value", pixels);
  });

  var canvas = document.getElementById("seat_canvas");
  var ctx = canvas.getContext("2d");

  // get params from the hidden input
  let params = JSON.parse(document.getElementById("id_canvas_params").value)

  cellSize = params.cellSize;
  pickedColor = params.pickedColor;
  notPickedColor = params.notPickedColor;

  // draw old seats
  params.oldSeats.forEach(seat => {
    currentSeats.push(seat);
  });

  redrawCanvas();

  let lastHoveredCell = null;
  canvas.addEventListener('mousemove', event => {
    const bounding = canvas.getBoundingClientRect();
    const x = event.clientX - bounding.left;
    const y = event.clientY - bounding.top;

    // calculate the grid cell coordinates
    const gridX = Math.floor(x / cellSize);
    const gridY = Math.floor(y / cellSize);

    // if the mouse has moved to a new cell, redraw
    if (lastHoveredCell === null || gridX !== lastHoveredCell.x || gridY !== lastHoveredCell.y) {
      redrawCanvas();

      // draw the outline on the current cell
      ctx.strokeStyle = 'red'; // color of the outline
      ctx.lineWidth = 2; // width of the outline
      ctx.strokeRect(gridX * cellSize, gridY * cellSize, cellSize, cellSize);

    }
  });

  canvas.addEventListener('click', event => {
    const bounding = canvas.getBoundingClientRect();
    const x = event.clientX - bounding.left;
    const y = event.clientY - bounding.top;

    // calculate the grid cell coordinates
    const gridX = Math.floor(x / cellSize);
    const gridY = Math.floor(y / cellSize);

    if (currentSeats.some(seat => seat[0] === gridX && seat[1] === gridY)) {
      currentSeats = currentSeats.filter(seat => seat[0] !== gridX || seat[1] !== gridY);
    } else {
      currentSeats.push([gridX, gridY]);
    }

    redrawCanvas();
  });
}
