using DTOs.Auth;
using Entities;
using Microsoft.AspNetCore.Identity;
using Microsoft.AspNetCore.Mvc;
using Swashbuckle.AspNetCore.Annotations;

namespace StarWars.Api.Controllers
{
    [ApiController]
    [Route("api/[controller]")]
    [SwaggerTag("Gestión de autenticación y registro de usuarios.")]
    public class AuthController(UserManager<User> userManager, SignInManager<User> signInManager) : ControllerBase
    {

        [HttpPost("register")]
        [SwaggerOperation(Summary = "Registra un nuevo usuario en la base de datos.")]
        public async Task<ActionResult<AuthResponseDto>> Registro([FromBody] RegisterDto dto)
        {
            //buscar correo electronico
            var existeUsuario = await userManager.FindByEmailAsync(dto.Email);

            if (existeUsuario != null)
            {
                return BadRequest(new AuthResponseDto
                {
                    IsSuccess = false,
                    Message = "El correo electrónico ya fue registrado"
                });
            }            

            // se mapean datos del dto a la entidad User
            var user = new User
            {
                Email = dto.Email,
                UserName = !string.IsNullOrWhiteSpace(dto.UserName) ? dto.UserName : dto.Email,
                FullName = dto.FullName
            };
            
            // con createAsync, crea el usuario y Identity encripta la contraseña automaticamente
            var result = await userManager.CreateAsync(user, dto.Password!);

            if (!result.Succeeded)
            {
                // Identity rechaza un registro y hace una consultaq LINQ para extraer los mensajes de error y unirlos con ", "
                var errors = string.Join(", ", result.Errors.Select(e => e.Description));

                return BadRequest(new AuthResponseDto
                {
                    IsSuccess = false,
                    Message = $"Error al registrar usuario: {errors}"
                });
            }

            return Ok(new AuthResponseDto
            {
                IsSuccess = true,
                Message = "Usuario registrado correctamente.",
                Email = user.Email,
                FullName = user.FullName
            });

        }

        [HttpPost("login")]
        [SwaggerOperation(Summary = "Inicia sesión verificando credenciales.")]
        public async Task<ActionResult<AuthResponseDto>> Login([FromBody] LoginDto dto)
        {
            // buscar correo electronico
            var busquedaUser = await userManager.FindByEmailAsync(dto.Email);

            if (busquedaUser == null)
            {
                //crea un objeto unauthorized que retorna respuesta con codigo 401
                return Unauthorized(new AuthResponseDto
                {
                    IsSuccess = false,
                    Message = "El usuario o la contraseña son incorrectos."
                });
            }
            // Valida si la contraseña enviada coincide con el hash almacenado con el método CheckPasswordSignInAsync
            // el parámetro lockoutOnFailure indica si el usuario deberia ser bloqueado por si el ingreso falla            
            var signInResult = await signInManager.CheckPasswordSignInAsync(busquedaUser, dto.Password, lockoutOnFailure: false);

            if (!signInResult.Succeeded)
            {
                return Unauthorized(new AuthResponseDto
                {
                    IsSuccess = false,
                    Message = "Usuario o contraseña incorrectos."
                });
            }
            // 3. Credenciales correctas: devolver respuesta exitosa
            return Ok(new AuthResponseDto
            {
                IsSuccess = true,
                Message = "Inicio de sesión exitoso.",
                Email = busquedaUser.Email,
                FullName = busquedaUser.FullName
            });
        }
    }
}
