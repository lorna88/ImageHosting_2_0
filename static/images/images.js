fetch('http://localhost:8000/images')
    .then(response => response.json())
    .then(data => {
        const imagesContainer = document.getElementById('images');
        data.images.forEach(image => {
            image_name = image.filename + image.file_type;
            const div = document.createElement('div');
            div.classList.add('col-lg-3', 'col-md-4', 'col-xs-6', 'thumb')
            imagesContainer.appendChild(div);

            const a = document.createElement('a');
            a.href = `/images/${image_name}`;
            div.appendChild(a);

            const imageElement = document.createElement('img');
            imageElement.src = `/images/${image_name}`;
            imageElement.alt = image_name;
            imageElement.classList.add('zoom', 'img-fluid')

            imageElement.onmouseover = function(event) {
                let target = event.target;
                target.classList.add('transition');
            };

            imageElement.onmouseout = function(event) {
                let target = event.target;
                target.classList.remove('transition');
            };

            a.appendChild(imageElement);
        });
    })