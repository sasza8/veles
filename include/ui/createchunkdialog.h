/*
 * Copyright 2016 CodiLime
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 * http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 *
 */
#ifndef CREATECHUNKDIALOG_H
#define CREATECHUNKDIALOG_H

#include <QDialog>
#include <QItemSelectionModel>
#include <QtCore>

#include "ui/fileblobmodel.h"

namespace Ui {
class CreateChunkDialog;
}

namespace veles {
namespace ui {

class CreateChunkDialog : public QDialog {
  Q_OBJECT

 public:
  explicit CreateChunkDialog(FileBlobModel *chunksModel_,
                             QItemSelectionModel *selectionModel = nullptr,
                             QWidget *parent_ = 0);
  ~CreateChunkDialog();
  Ui::CreateChunkDialog *ui;
  void updateParent(bool childOfSelected = false);
  void setRange(uint64_t begin, uint64_t end);

 public slots:
  virtual void accept();
  virtual void updateBinDataSize();

 private:
  FileBlobModel *chunksModel_;
  QItemSelectionModel *chunkSelectionModel_;
  bool useChildOfSelected_;
  void init();
  void displayPath();
  QModelIndex parentChunk();
};

}  // namespace ui
}  // namespace veles

#endif  // CREATECHUNKDIALOG_H
