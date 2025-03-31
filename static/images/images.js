fetch('http://localhost:8000/images')
    .then(response => response.json())
    .then(data => {
        const imagesContainer = document.getElementById('images');
        data.images.forEach(image => {
            // получаем имя файла
            image_name = image.filename + image.file_type;

            // добавляем карточку картинки
            const div = document.createElement('div');
            div.classList.add('col-lg-3', 'col-md-4', 'col-xs-6', 'thumb')
            imagesContainer.appendChild(div);
            const card = document.createElement('div');
            card.classList.add('card');
            div.appendChild(card)

            // добавляем картинку в ссылке вверху карточки
            const a = document.createElement('a');
            a.href = `/images/${image_name}`;
            card.appendChild(a);
            const imageElement = document.createElement('img');
            imageElement.src = `/images/${image_name}`;
            imageElement.alt = image_name;
            imageElement.classList.add('zoom', 'img-fluid', 'card-img-top')

            imageElement.onmouseover = function(event) {
                let target = event.target;
                target.classList.add('transition');
            };
            imageElement.onmouseout = function(event) {
                let target = event.target;
                target.classList.remove('transition');
            };

            a.appendChild(imageElement);

            // добавляем описание под картинкой
            const card_body = document.createElement('div');
            card_body.classList.add('card-body');
            card.appendChild(card_body)

            const link = document.createElement('a');
            link.classList.add('card-link');
            link.href = `/images/${image_name}`;
            link.textContent = image.original_name + image.file_type;
            card_body.appendChild(link);

            const deleteButton = document.createElement('button');
            deleteButton.onclick = () => {
                fetch('/delete', {
                    method: 'DELETE',
                    headers: {
                        'Filename': image_name
                    }
                })
                .then(data => {
                    location.reload();
                })
                .catch(error => console.error(error));
            }
            deleteButton.innerHTML = '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10" fill="currentColor" class="bi bi-x-lg" viewBox="0 0 16 16"> <path d="M2.146 2.854a.5.5 0 1 1 .708-.708L8 7.293l5.146-5.147a.5.5 0 0 1 .708.708L8.707 8l5.147 5.146a.5.5 0 0 1-.708.708L8 8.707l-5.146 5.147a.5.5 0 0 1-.708-.708L7.293 8z"/></svg>';
            deleteButton.classList.add('delete-btn', 'ml-2', 'd-inline-flex');
            card_body.appendChild(deleteButton);

            const size = document.createElement('p');
            size.classList.add('card-text');
            size.textContent = image.size + ' KB';
            card_body.appendChild(size);

            const date = document.createElement('p');
            date.classList.add('card-text');
            date.textContent = image.upload_date;
            card_body.appendChild(date);
        });
    })