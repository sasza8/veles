/*
 * Copyright 2017 CodiLime
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
#include <QAction>
#include <QColorDialog>
#include <QFileDialog>
#include <QGroupBox>
#include <QHeaderView>
#include <QLineEdit>
#include <QMessageBox>
#include <QPushButton>
#include <QStandardItemModel>
#include <QToolBar>
#include <QTreeView>
#include <QVBoxLayout>

#include "dbif/info.h"
#include "dbif/types.h"
#include "dbif/universe.h"

#include "ui/hexeditwidget.h"
#include "ui/nodetreewidget.h"
#include "ui/nodewidget.h"
#include "ui/veles_mainwindow.h"

#include "util/settings/hexedit.h"
#include "util/icons.h"

#include "visualisation/panel.h"

namespace veles {
namespace ui {

/*****************************************************************************/
/* Public methods */
/*****************************************************************************/

NodeWidget::NodeWidget(MainWindowWithDetachableDockWidgets *main_window,
    QSharedPointer<FileBlobModel>& data_model,
    QSharedPointer<QItemSelectionModel>& selection_model)
    : View("Hex editor", ":/images/show_hex_edit.png"),
      main_window_(main_window), data_model_(data_model),
      selection_model_(selection_model), sampler_(nullptr) {
  hex_edit_widget_ = new HexEditWidget(
      main_window, data_model, selection_model);
  setCentralWidget(hex_edit_widget_);

  node_tree_dock_ = new QDockWidget;
  node_tree_widget_ = new NodeTreeWidget(main_window, data_model,
      selection_model);
  node_tree_dock_->setWidget(node_tree_widget_);
  node_tree_dock_->setAllowedAreas(
      Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);
  setDockNestingEnabled(true);
  addDockWidget(Qt::LeftDockWidgetArea, node_tree_dock_);

  minimap_dock_ = new QDockWidget;
  minimap_ = new visualisation::MinimapPanel(this);

  if(data_model_->binData().size() > 0) {
    loadBinDataToMinimap();
  } else {
    sampler_data_ = QByteArray("");
    sampler_ = new util::UniformSampler(sampler_data_);
    sampler_->setSampleSize(4096 * 1024);
    minimap_->setSampler(sampler_);
  }

  minimap_dock_->setWidget(minimap_);
  minimap_dock_->setAllowedAreas(
      Qt::LeftDockWidgetArea | Qt::RightDockWidgetArea);
  MainWindowWithDetachableDockWidgets::splitDockWidget2(this, node_tree_dock_,
      minimap_dock_, Qt::Horizontal);
  minimap_dock_->hide();

  connect(hex_edit_widget_, &HexEditWidget::showNodeTree,
      node_tree_dock_, &QDockWidget::setVisible);
  connect(hex_edit_widget_, &HexEditWidget::showMinimap,
        minimap_dock_, &QDockWidget::setVisible);
  connect(data_model_.data(), &FileBlobModel::newBinData,
      this, &NodeWidget::loadBinDataToMinimap);
  connect(node_tree_dock_, &QDockWidget::visibilityChanged,
      hex_edit_widget_, &HexEditWidget::nodeTreeVisibilityChanged);
  connect(minimap_dock_, &QDockWidget::visibilityChanged,
      hex_edit_widget_, &HexEditWidget::minimapVisibilityChanged);
}

NodeWidget::~NodeWidget() {
  delete sampler_;
}

void NodeWidget::loadBinDataToMinimap() {
  if(sampler_) {
    delete sampler_;
  }

  sampler_data_ = QByteArray((const char *)data_model_->binData().rawData(),
          static_cast<int>(data_model_->binData().octets()));
  sampler_ = new util::UniformSampler(sampler_data_);
  sampler_->setSampleSize(4096 * 1024);
  minimap_->setSampler(sampler_);
}

}  // namespace ui
}  // namespace veles
