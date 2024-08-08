const gridSize = 25; // size of each grid cell
const pickedColor = "blue";
const notPickedColor = "white";
let currentSeats = [];

function drawGrid() {
  const canvas = document.getElementById("seatCanvas");
  const ctx = canvas.getContext("2d");

  const gridCount = canvas.width / gridSize; // number of grid cells

  ctx.strokeStyle = 'black'; // color of the grid lines

  // draw the grid
  for (let i = 0; i <= gridCount; i++) {
    // vertical lines
    ctx.beginPath();
    ctx.moveTo(i * gridSize, 0);
    ctx.lineTo(i * gridSize, canvas.height);
    ctx.stroke();

    // horizontal lines
    ctx.beginPath();
    ctx.moveTo(0, i * gridSize);
    ctx.lineTo(canvas.width, i * gridSize);
    ctx.stroke();
  }
}

function placePixel(ctx, gridX, gridY, color) {
  ctx.fillStyle = color;
  // offsets to keep grid lines
  ctx.fillRect(gridX * gridSize + 1, gridY * gridSize + 1, gridSize - 2, gridSize - 2);

  if (color === pickedColor) {
    currentSeats.push([gridX, gridY]);
  } else if (color === notPickedColor) {
    currentSeats = currentSeats.filter(seat => seat[0] !== gridX || seat[1] !== gridY);
  }
}

window.onload = function () {

  // set up form submission hook
  var form = document.getElementById("event_form");
  var canvasInput = document.createElement("input");
  canvasInput.setAttribute("name", "seats");
  canvasInput.setAttribute("type", "hidden");
  canvasInput.setAttribute("value", "");
  form.appendChild(canvasInput);

  form.addEventListener("submit", event => {
    pixels = JSON.stringify(currentSeats);
    canvasInput.setAttribute("value", pixels);
  });

  var canvas = document.getElementById("seatCanvas");
  var ctx = canvas.getContext("2d");

  // get old seats
  let oldSeats = document.getElementById("id_oldseats").value;
  JSON.parse(oldSeats).forEach(seat => {
    currentSeats.push(seat)
    placePixel(ctx, seat[0], seat[1], pickedColor);
  });

  let data = {
    lastHoveredCell: null,
    oldState: null,
  }

  drawGrid();

  canvas.addEventListener('mousemove', event => {
    const bounding = canvas.getBoundingClientRect();
    const x = event.clientX - bounding.left;
    const y = event.clientY - bounding.top;

    // calculate the grid cell coordinates
    const gridX = Math.floor(x / gridSize);
    const gridY = Math.floor(y / gridSize);

    let lastHoveredCell = data.lastHoveredCell;

    // if the mouse has moved to a new cell, redraw the grid
    if (lastHoveredCell === null || gridX !== lastHoveredCell.x || gridY !== lastHoveredCell.y) {
      // restore the canvas to its state before the outline was drawn
      if (data.oldState !== null) {
        ctx.putImageData(data.oldState, 0, 0);
      }

      // save the current state of the canvas
      const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);

      // draw the outline on the current cell
      ctx.strokeStyle = 'red'; // color of the outline
      ctx.lineWidth = 2; // width of the outline
      ctx.strokeRect(gridX * gridSize, gridY * gridSize, gridSize, gridSize);

      // store the current cell and the image data
      data.lastHoveredCell = { x: gridX, y: gridY };
      data.oldState = imageData
    }
  });


  canvas.addEventListener('click', event => {
    const bounding = canvas.getBoundingClientRect();
    const x = event.clientX - bounding.left;
    const y = event.clientY - bounding.top;

    // calculate the grid cell coordinates
    const gridX = Math.floor(x / gridSize);
    const gridY = Math.floor(y / gridSize);

    ctx.putImageData(data.oldState, 0, 0);

    // javascript is cursed
    let picked = currentSeats.some(seat => seat[0] === gridX && seat[1] === gridY);
    let color = picked ? notPickedColor : pickedColor;

    placePixel(ctx, gridX, gridY, color);

    // save the current state of the canvas
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    data.oldState = imageData
  });
}
