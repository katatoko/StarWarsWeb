using System;
using System.Collections.Generic;
using System.Text;

namespace Entities
{
    public class CharacterImage
    {
        public int Id { get; set; }

        //El id del personaje de SWAPI
        public long CharacterId { get; set; }

        //Nombre del archivo de imagen
        public string FileName { get; set; } = string.Empty;

        public string ContentType { get; set; } = string.Empty;

        //Guarda los bytes de la imagen directamente en PostgreSQL (tipo bytea)
        public byte[] Data { get; set; } = [];

        public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    }
}
