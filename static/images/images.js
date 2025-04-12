const imagesContainer = document.getElementById('images');
const imagesPerPage = 12;
let params = new URLSearchParams(document.location.search);
let currentPage = params.get('page') ?? 1;

function setImages(images) {
  images.forEach(image => {
    const fullFilename = image.filename + image.file_type;

    const imageBlock = document.createElement('div');
    const card = document.createElement('div');
    const imageLink = document.createElement('a');
    const imageElement = document.createElement('img');
    const card_body = document.createElement('div');
    const row = document.createElement('div');
    const colOrigName = document.createElement('div');
    const colDelete = document.createElement('div');
    const origName = document.createElement('a');
    const deleteButton = document.createElement('button');
    const size = document.createElement('p');
    const date = document.createElement('p');

    imageBlock.classList.add('col-lg-3', 'col-md-4', 'col-xs-6', 'thumb')
    card.classList.add('card');
    imageElement.classList.add('zoom', 'img-fluid', 'card-img-top')
    card_body.classList.add('card-body');
    row.classList.add('row');
    colOrigName.classList.add('col-9', 'text-truncate');
    colDelete.classList.add('col');
    origName.classList.add('card-link');
    deleteButton.classList.add('delete-btn', 'ml-2', 'd-inline-flex');
    size.classList.add('card-text');
    date.classList.add('card-text');

    imagesContainer.appendChild(imageBlock);
    imageBlock.appendChild(card);
    card.appendChild(imageLink);
    imageLink.appendChild(imageElement);
    card.appendChild(card_body);
    row.appendChild(colOrigName)
    row.appendChild(colDelete)
    card_body.appendChild(row)
    colOrigName.appendChild(origName);
    colDelete.appendChild(deleteButton);
    card_body.appendChild(size);
    card_body.appendChild(date);

    origName.href = `/images/${fullFilename}`;
    origName.textContent = image.original_name + image.file_type;
    origName.title = image.original_name + image.file_type;
    size.textContent = image.size + ' KB';
    date.textContent = image.upload_date;

    imageLink.href = `/images/${fullFilename}`;
    imageElement.src = `/images/${fullFilename}`;
    imageElement.alt = fullFilename;
    imageElement.onmouseover = function(event) {
        let target = event.target;
                target.classList.add('transition');
    };
    imageElement.onmouseout = function(event) {
        let target = event.target;
        target.classList.remove('transition');
    };

    deleteButton.onclick = () => {
        fetch(`/api/delete/${fullFilename}`, { method: 'DELETE' })
        .then(() => loadImages(currentPage))
        .catch(error => console.error(error));
    }
    deleteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" fill="currentColor" class="bi bi-x-lg" viewBox="0 0 16 16"> <path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8z"/></svg>';
    })
}

function loadImages(page) {
  fetch(`/api/images/?page=${page}`)
    .then(response => response.json())
    .then(data => {
      page = data.page;
      currentPage = data.page;
      history.pushState(null, null, `/images/?page=${page}`);
      if (data.images.length == 0) {
          document.querySelector('nav').style.display = 'none';
          document.querySelector('.container').style.display = 'none';
          const none_images = document.createElement('h1')
          none_images.classList.add('text-center')
          document.body.appendChild(none_images).textContent = 'Нет загруженных изображений';
      } else {
          imagesContainer.innerHTML = '';
          setImages(data.images);
          document.getElementById('nextPage').disabled = data.last_page;
          document.getElementById('prevPage').disabled = page === 1;
          document.getElementById('currentPage').textContent = page;
      }
    })
    .catch(error => console.error(error));
}

// Обработчики кликов для кнопок пагинации
document.getElementById('prevPage').addEventListener('click', () => {
  if (currentPage > 1) {
    loadImages(currentPage - 1);
  }
});

document.getElementById('nextPage').addEventListener('click', () => {
  loadImages(currentPage + 1);
});

loadImages(currentPage);