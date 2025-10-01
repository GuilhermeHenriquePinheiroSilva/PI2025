import { Component } from '@angular/core';
import { FooterComponent } from '../shared/footer/footer.component';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';

import { HttpClient } from '@angular/common/http';
import { Router } from '@angular/router';
import { Enterprise } from '../../models/enterprise.model';
import { NotificationService } from '../../../services/notification.service';

@Component({
  selector: 'app-gc-guide',
  standalone: true,
  imports: [CommonModule, FormsModule, FooterComponent],
  templateUrl: './gc-guide.component.html',
  styleUrls: ['./gc-guide.component.css']
})
export class GcGuideComponent {
  enterprise: Enterprise = {
    nome_fantasia: '',
    cnpj: '',
    nome_admin_empresa: '',
    cpf_adm: '',
    telefone: ''
  };

  constructor(private http: HttpClient, private router: Router, private notificationService: NotificationService) {}

  onSubmit() {
    // A rota precisa ser protegida, então o token do usuário será enviado automaticamente pelo interceptor
    this.http.post('http://localhost:8000/enterprise/register', this.enterprise)
      .subscribe({
        next: (response) => {
          console.log('Empresa cadastrada com sucesso!', response);
          this.notificationService.show('Empresa cadastrada com sucesso! Você será redirecionado para o seu perfil.', "success");
          this.router.navigate(['/user-profile']);
        },
        error: (error) => {
          console.error('Erro ao cadastrar empresa', error);
          alert(`Erro: ${error.error.detail}`);
        }
      });
  }
}