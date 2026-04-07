#ifndef SINGLEMODELPREVIEW_H
#define SINGLEMODELPREVIEW_H

#include "../../Converters/IModelConverter.h"
#include <QMouseEvent>
#include <QOpenGLWidget>
#include <QVector3D>
#include <QWheelEvent>
#if defined(__APPLE__)
#include <GLUT/glut.h>
#elif defined(_WIN32)
#include <GL/freeglut.h>
#else
#include <GL/glut.h>
#endif

struct Mouse {
    int X;
    int Y;
};
struct Camera {
    float X;
    float Y;
    float Z;
    float angleX;
    float angleY;
};

class SingleModelPreview : public QOpenGLWidget {
Q_OBJECT
public:
    explicit SingleModelPreview(Model *model, QWidget *parent = nullptr);
    ~SingleModelPreview() override;
private slots:
    void onReplaced(Model *model);
private:
    Model *model;
    Camera camera{};
    Mouse mouse{};
    void initializeGL() override;
    void paintGL() override;
    void mousePressEvent(QMouseEvent *event) override;
    void mouseMoveEvent(QMouseEvent *event) override;
    void wheelEvent(QWheelEvent *event) override;
};

#endif // SINGLEMODELPREVIEW_H
