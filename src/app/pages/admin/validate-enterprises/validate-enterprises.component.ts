// Front/src/app/pages/admin/validate-enterprises/validate-enterprises.component.ts

import { Component, OnInit } from '@angular/core';
import { Enterprise } from '../../../models/enterprise.model';
import { EnterpriseService } from '../../../../services/enterprise.service';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';

@Component({
  selector: 'app-validate-enterprises',
  standalone: true, 
  imports: [
    CommonModule, 
    FormsModule   
  ],
  templateUrl: './validate-enterprises.component.html',
  styleUrls: ['./validate-enterprises.component.css'] 
})
export class ValidateEnterprisesComponent implements OnInit {
  pendingEnterprises: Enterprise[] = [];
  
  isRejectionModalVisible = false;
  rejectionReason = '';
  enterpriseToRejectId: number | null = null;
  isLoading = false;

  constructor(private enterpriseService: EnterpriseService) { }

  ngOnInit(): void {
    this.loadPendingEnterprises();
  }

  loadPendingEnterprises(): void {
    this.enterpriseService.getPendingEnterprises().subscribe({
      next: (data) => this.pendingEnterprises = data,
      error: (err) => console.error('Erro ao buscar empresas pendentes', err)
    });
  }

  approve(enterpriseId: number): void {
    this.enterpriseService.approveEnterprise(enterpriseId).subscribe({
      next: () => this.loadPendingEnterprises(),
      error: (err) => console.error('Erro ao aprovar empresa', err)
    });
  }

  // --- ADICIONE ESTAS NOVAS FUNÇÕES ---

  // 1. Abre o pop-up
  openRejectionModal(enterpriseId: number): void {
    this.enterpriseToRejectId = enterpriseId;
    this.isRejectionModalVisible = true;
  }

  // 2. Fecha o pop-up e limpa os dados
  cancelRejection(): void {
    this.isRejectionModalVisible = false;
    this.rejectionReason = '';
    this.enterpriseToRejectId = null;
  }

  // 3. Confirma a rejeição e chama o serviço
  confirmRejection(): void {
    if (!this.rejectionReason.trim()) {
      alert('Por favor, insira um motivo para a rejeição.');
      return;
    }

    if (this.enterpriseToRejectId) {
      this.enterpriseService.rejectEnterprise(this.enterpriseToRejectId, this.rejectionReason)
        .subscribe({
          next: () => {
            this.cancelRejection(); // Fecha o pop-up
            this.loadPendingEnterprises(); // Recarrega a lista
          },
          error: (err) => console.error('Erro ao rejeitar empresa', err)
        });
    }
  }
}