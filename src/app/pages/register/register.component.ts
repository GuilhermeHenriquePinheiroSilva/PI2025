import { Component } from '@angular/core';
import { Router, RouterLink } from '@angular/router';
import { AuthService } from '../../../services/auth.service';
import { User } from '../../models/user.model';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-register',
  standalone: true,
  imports: [CommonModule, FormsModule, RouterLink],
  templateUrl: './register.component.html',
  styleUrls: ['./register.component.css'],
})
export class RegisterComponent {
  user: User = { username: '', email: '', password: '', role: 'user' };
  successMessage: string = '';
  errorMessage: string = '';

  constructor(private authService: AuthService, private router: Router) {}

  onSubmit() {
    console.log('Formulário enviado', this.user);

    this.authService.register(this.user).subscribe({
      next: (response) => {
        console.log('Usuário cadastrado com sucesso:', response);
        this.successMessage = 'Cadastro realizado com sucesso! Redirecionando...';
        this.errorMessage = ''; // limpa qualquer erro anterior

        setTimeout(() => {
          this.router.navigate(['/login']);
        }, 2000); // redireciona após 2 segundos
      },
      error: (error) => {
        console.error('Erro no cadastro', error);
        this.errorMessage = 'Erro ao cadastrar. Verifique os dados.';
        this.successMessage = ''; // limpa qualquer sucesso anterior
      }
    });
  }
}
