const gridSize = 25; // size of each grid cell
const pickedColor = "blue";
const notPickedColor = "white";

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

function getPixelColor(ctx, gridX, gridY) {
  // get the color of the top-left pixel of the clicked cell
  const imageData = ctx.getImageData(gridX * gridSize + 2, gridY * gridSize + 2, 1, 1);
  return imageData.data;
}

function placePixel(ctx, gridX, gridY, color) {
  // offsets to keep grid lines
  ctx.fillStyle = color;
  ctx.fillRect(gridX * gridSize + 1, gridY * gridSize + 1, gridSize - 2, gridSize - 2);
}

function cssColorToRGBA(color) {
  // create a temporary div
  var div = document.createElement("div");
  div.style.color = color;
  document.body.appendChild(div);

  // get the computed color value
  var computedColor = window.getComputedStyle(div).color;

  // remove the div after getting the computed color
  document.body.removeChild(div);

  // convert the computed color to RGBA
  var rgba = computedColor.replace(/rgba?\(([^)]+)\)/, '$1').split(',').map(function (num) {
    return parseInt(num, 10);
  });

  // if the color was in RGB format, add an alpha value of 255
  if (rgba.length === 3) {
    rgba.push(255);
  }

  return rgba;
}

function getPixelsFromCanvas(canvas) {
  let maxGridX = canvas.width / gridSize;
  let maxGridY = canvas.height / gridSize;
  let ctx = canvas.getContext("2d");
  let picked = cssColorToRGBA(pickedColor)

  let res = [];
  for (let x = 0; x < maxGridX; x++) {
    for (let y = 0; y < maxGridY; y++) {
      let pixelColor = Array.from(getPixelColor(ctx, x, y));

      if (pixelColor.every((v, i) => v == picked[i])) {
        res.push([x, y]);
      }
    }
  }

  return res;
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
    let pixels = getPixelsFromCanvas(canvas);
    pixels = JSON.stringify(pixels);
    canvasInput.setAttribute("value", pixels);
  });

  var canvas = document.getElementById("seatCanvas");
  var ctx = canvas.getContext("2d");

  // get old seats
  let oldSeats = document.getElementById("id_oldseats").value;
  JSON.parse(oldSeats).forEach(seat => {
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

    let pixelColor = Array.from(getPixelColor(ctx, gridX, gridY));
    let picked = cssColorToRGBA(pickedColor)

    let color;
    // javascript is cursed
    if (pixelColor.every((v, i) => v == picked[i])) {
      // if it is, fill the cell with white
      color = notPickedColor;
    } else {
      // if it's not, fill the cell with blue
      color = pickedColor;
    }

    placePixel(ctx, gridX, gridY, color);
    // offsets to keep grid lines
    ctx.fillRect(gridX * gridSize + 1, gridY * gridSize + 1, gridSize - 2, gridSize - 2);

    // save the current state of the canvas
    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    data.oldState = imageData
  });
}
