import React, { useState, useRef } from 'react';
import { UploadCloud, File, AlertCircle, CheckCircle2 } from 'lucide-react';
import { Button } from '../common/Button';
import { apiClient } from '../../api/client';
import { DocumentCategory } from '../../api/types';

interface UploadDropzoneProps {
  onSuccess: () => void;
}

export const UploadDropzone: React.FC<UploadDropzoneProps> = ({ onSuccess }) => {
  const [dragActive, setDragActive] = useState<boolean>(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [category, setCategory] = useState<DocumentCategory>('product_manual');
  const [uploading, setUploading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string>('');
  const [successMsg, setSuccessMsg] = useState<string>('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const allowedExtensions = ['.pdf', '.txt', '.md'];
  const maxSizeBytes = 10 * 1024 * 1024; // 10MB

  const validateFile = (file: File): boolean => {
    setErrorMsg('');
    setSuccessMsg('');

    const ext = file.name.substring(file.name.lastIndexOf('.')).toLowerCase();
    if (!allowedExtensions.includes(ext)) {
      setErrorMsg(`Invalid file type '${ext}'. Only .pdf, .txt, and .md files are supported.`);
      return false;
    }

    if (file.size > maxSizeBytes) {
      setErrorMsg(`File size ${(file.size / (1024 * 1024)).toFixed(1)}MB exceeds maximum 10MB limit.`);
      return false;
    }

    return true;
  };

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === 'dragenter' || e.type === 'dragover') {
      setDragActive(true);
    } else if (e.type === 'dragleave') {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const file = e.target.files[0];
      if (validateFile(file)) {
        setSelectedFile(file);
      }
    }
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setErrorMsg('');
    setSuccessMsg('');

    try {
      const res = await apiClient.uploadDocument(selectedFile, category);
      setSuccessMsg(`Document '${res.filename}' uploaded and indexed (${res.chunk_count} chunks generated).`);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      onSuccess();
    } catch (err: any) {
      setErrorMsg(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="p-6 rounded-2xl bg-[#151D32] border border-slate-700/70 shadow-xl space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-base font-bold text-slate-100">Upload Knowledge Document</h3>
          <p className="text-xs text-slate-400 mt-0.5">
            Ingest technical manuals, troubleshooting sheets, or warranty policies into ChromaDB & BM25.
          </p>
        </div>
      </div>

      {/* Drag & Drop Zone */}
      <div
        onDragEnter={handleDrag}
        onDragLeave={handleDrag}
        onDragOver={handleDrag}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`border-2 border-dashed rounded-xl p-8 text-center cursor-pointer transition-all duration-200 ${
          dragActive
            ? 'border-indigo-400 bg-indigo-500/10'
            : selectedFile
            ? 'border-emerald-500/50 bg-emerald-950/20'
            : 'border-slate-700 hover:border-slate-600 bg-slate-900/50'
        }`}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept=".pdf,.txt,.md"
          onChange={handleFileChange}
          className="hidden"
        />

        {selectedFile ? (
          <div className="space-y-2">
            <div className="w-12 h-12 rounded-full bg-emerald-500/20 text-emerald-400 flex items-center justify-center mx-auto">
              <File className="w-6 h-6" />
            </div>
            <div className="font-semibold text-slate-200 text-sm">{selectedFile.name}</div>
            <div className="text-xs text-slate-400">
              {(selectedFile.size / 1024).toFixed(1)} KB • Ready for Ingestion
            </div>
          </div>
        ) : (
          <div className="space-y-2">
            <div className="w-12 h-12 rounded-full bg-indigo-500/10 text-indigo-400 flex items-center justify-center mx-auto">
              <UploadCloud className="w-6 h-6" />
            </div>
            <div className="font-semibold text-slate-200 text-sm">
              Click to browse or drag & drop document
            </div>
            <div className="text-xs text-slate-400">
              Supports PDF, Plain Text (.txt), or Markdown (.md) up to 10MB
            </div>
          </div>
        )}
      </div>

      {/* Category selector & Upload button */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-4 pt-2">
        <div className="flex items-center gap-2 w-full sm:w-auto">
          <label className="text-xs font-semibold text-slate-300 whitespace-nowrap">
            Document Category:
          </label>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value as DocumentCategory)}
            className="text-xs bg-slate-900 border border-slate-700 rounded-xl px-3 py-2 text-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 w-full sm:w-auto"
          >
            <option value="product_manual">product_manual (User Manuals & Specs)</option>
            <option value="troubleshooting">troubleshooting (Error Codes & Fixes)</option>
            <option value="warranty">warranty (Warranty Policies & SLAs)</option>
            <option value="faq">faq (Customer Support FAQs)</option>
          </select>
        </div>

        <Button
          type="button"
          variant="gradient"
          size="md"
          disabled={!selectedFile || uploading}
          loading={uploading}
          onClick={handleUpload}
          className="w-full sm:w-auto"
        >
          {uploading ? 'Ingesting Document...' : 'Ingest to Knowledge Base'}
        </Button>
      </div>

      {/* Messages */}
      {errorMsg && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-rose-950/60 border border-rose-500/30 text-rose-300 text-xs">
          <AlertCircle className="w-4 h-4 flex-shrink-0" />
          <span>{errorMsg}</span>
        </div>
      )}

      {successMsg && (
        <div className="flex items-center gap-2 p-3 rounded-xl bg-emerald-950/60 border border-emerald-500/30 text-emerald-300 text-xs">
          <CheckCircle2 className="w-4 h-4 flex-shrink-0" />
          <span>{successMsg}</span>
        </div>
      )}
    </div>
  );
};
