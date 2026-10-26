using System;
using System.Collections.Generic;
using System.ComponentModel.DataAnnotations;
using System.Text;

namespace DTOs.Auth
{
    public class RegisterDto
    {
        [Display(Name = "Nombre Completo")]
        [Required(ErrorMessage = "El nombre completo es requerido.")]
        public string? FullName { get; set; }

        [Display(Name = "Nombre de Usuario")]
        [Required(ErrorMessage = "El nombre de usuario es obligatorio")]
        public string? UserName { get; set; }

        [Required(ErrorMessage = "El correo electrónico es requerido.")]
        [EmailAddress(ErrorMessage = "El formato del correo no es válido.")]
        public string? Email { get; set; }

        [Required(ErrorMessage = "La contraseña es requerida.")]
        [MinLength(6, ErrorMessage = "La contraseña debe tener al menos 6 caracteres.")]
        public string? Password { get; set; }
    }
}
